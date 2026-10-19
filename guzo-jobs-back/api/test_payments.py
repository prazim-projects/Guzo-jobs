"""Synthetic provider fixtures: no personal receipts, real money, or live HTTP."""
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
import json
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase
from django.utils import timezone

from .models import Contract, EscrowPayment, EscrowRecipient, Notification
from .payments import fund_escrow
from .receipts import (ReceiptError, account_matches, receipt_url, parse_receipt,
                       verify_receipt, fetch_receipt, NoRedirect, MAX_RECEIPT_BYTES)
from .test_audit import AuditFixture

CBE_URL = 'https://mbreciept.cbe.com.et/v2-SYNTHETIC12345'
TELE_URL = 'https://transactioninfo.ethiotelecom.et/receipt/TEST123456'


def cbe_payload(**overrides):
    data = dict(id='FTTEST123456', creditAccountHolder='Escrow Test Account', creditAccountNo='1********1234',
                creditCurrency='ETB', amountCredited='100.00', amountDebited='102.00',
                dateTimes=[timezone.now().isoformat()], encodedReceipt=CBE_URL, status='COMPLETED')
    data.update(overrides)
    return json.dumps(data).encode()


def tele_payload(**overrides):
    data = dict(name='Escrow Test Account', account='2519****1234', status='Completed',
                date=timezone.localtime(timezone.now(), timezone.get_fixed_timezone(180)).strftime('%d-%m-%Y %H:%M:%S'), amount='100')
    data.update(overrides)
    # The provider omits the closing td before its status value.
    return f'''<table><tr><td>Credited Party name</td><td>{data['name']}</td></tr>
    <tr><td>Credited party account no</td><td>{data['account']}</td></tr>
    <tr><td>transaction status<td>{data['status']}</td></tr>
    <tr><td>Invoice No.</td><td>Payment date</td><td>Settled Amount</td></tr>
    <tr><td>TEST123456</td><td>{data['date']}</td><td>{data['amount']} Birr</td></tr>
    <tr><td>Total Paid Amount</td><td>102 Birr</td></tr></table>'''.encode()


class ReceiptParserTests(SimpleTestCase):
    def test_cbe_uses_credited_principal_not_fee_inclusive_debit(self):
        receipt = parse_receipt(cbe_payload(), 'application/json', 'CBE')
        self.assertEqual(receipt.amount, Decimal('100'))
        self.assertEqual(receipt.reference, 'FTTEST123456')

    def test_telebirr_handles_real_world_missing_td_and_principal(self):
        receipt = parse_receipt(tele_payload(), 'text/html', 'TELEBIRR')
        self.assertEqual(receipt.status, 'COMPLETED')
        self.assertEqual(receipt.amount, Decimal('100'))
        self.assertEqual(receipt.recipient_name, 'Escrow Test Account')

    def test_cbe_rejects_invalid_or_missing_fields(self):
        for values in [dict(creditAccountHolder=''), dict(creditAccountNo=None), dict(amountCredited='NaN'),
                       dict(amountCredited='100.001'), dict(creditCurrency='USD'), dict(dateTimes=[]), dict(id=''),
                       dict(dateTimes=['2026-10-15T10:00:00']), dict(isOtherBank=True)]:
            with self.subTest(values=values), self.assertRaises(ReceiptError):
                parse_receipt(cbe_payload(**values), 'application/json', 'CBE')

    def test_account_comparison_checks_prefix_suffix_and_full_values(self):
        self.assertTrue(account_matches('1****1234', '1000000001234', 'CBE'))
        self.assertTrue(account_matches('2519****1234', '0910001234', 'TELEBIRR'))
        for value in ['****1234', '2****1234', '1****5678', '', '1000000001235']:
            self.assertFalse(account_matches(value, '1000000001234', 'CBE'))

    def test_url_allowlist_blocks_unsafe_destinations(self):
        with patch('api.receipts.socket.getaddrinfo') as dns:
            for value in ['http://127.0.0.1/x', 'file:///etc/passwd', CBE_URL + '?url=http://localhost',
                          CBE_URL + '#test', CBE_URL.replace('.et/', '.et.evil.invalid/'),
                          CBE_URL.replace('https://', 'https://user@'), CBE_URL.replace('.et/', '.et:8443/'),
                          TELE_URL + '/../../admin', CBE_URL + '\n']:
                with self.subTest(value=value), self.assertRaises(ReceiptError):
                    fetch_receipt(value)
            dns.assert_not_called()

    def test_private_dns_is_rejected(self):
        with patch('api.receipts.socket.getaddrinfo', return_value=[(2, 1, 6, '', ('127.0.0.1', 443))]), self.assertRaises(ReceiptError):
            fetch_receipt(CBE_URL)

    def test_redirects_are_rejected(self):
        with self.assertRaises(ReceiptError):
            NoRedirect().redirect_request(None, None, 302, '', {}, 'http://127.0.0.1/')

    def test_response_size_and_type_are_bounded(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.headers.get_content_type.return_value = 'application/json'
        response.read.return_value = b'x' * (MAX_RECEIPT_BYTES + 1)
        with patch('api.receipts.socket.getaddrinfo', return_value=[(2, 1, 6, '', ('8.8.8.8', 443))]), patch('api.receipts.build_opener') as opener:
            opener.return_value.open.return_value = response
            with self.assertRaises(ReceiptError): fetch_receipt(CBE_URL)
            response.read.assert_called_once_with(MAX_RECEIPT_BYTES + 1)
            response.headers.get_content_type.return_value = 'text/javascript'
            with self.assertRaises(ReceiptError): fetch_receipt(CBE_URL)

    def test_blank_image_pdf_fails_closed(self):
        from pypdf import PdfWriter
        pdf = PdfWriter(); pdf.add_blank_page(width=200, height=200)
        output = BytesIO(); pdf.write(output)
        with self.assertRaisesRegex(ReceiptError, 'image'):
            parse_receipt(output.getvalue(), 'application/pdf', 'CBE')


class PaymentFlowTests(AuditFixture):
    def setUp(self):
        self.contract.status = 'ACCEPTED'; self.contract.save()
        self.recipient = EscrowRecipient.objects.create(provider='CBE', name='Escrow Test Account', account_number='1000000001234', is_active=True)

    def response(self, payload=None):
        return patch('api.receipts.fetch_receipt', return_value=('CBE', CBE_URL, payload or cbe_payload(), 'application/json'))

    def test_funds_and_records_immutable_evidence(self):
        with self.response(): payment = fund_escrow(self.owner, self.contract.pk, CBE_URL)
        self.assertEqual(payment.status, 'PAID')
        self.assertEqual(payment.verification_snapshot['account_match'], 'masked')
        self.assertEqual(len(payment.verification_snapshot['sha256']), 64)
        self.recipient.name = 'Changed Name'; self.recipient.save()
        payment.refresh_from_db()
        self.assertEqual(payment.verification_snapshot['recipient_name'], 'Escrow Test Account')
        self.assertEqual(Notification.objects.filter(type='ESCROW_PAID').count(), 1)

    def test_same_submission_is_idempotent(self):
        with self.response():
            first = fund_escrow(self.owner, self.contract.pk, CBE_URL)
            second = fund_escrow(self.owner, self.contract.pk, CBE_URL)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Notification.objects.filter(type='ESCROW_PAID').count(), 1)

    def test_graphql_funding_and_replay_rejection(self):
        query = f'mutation {{ initiateEscrowPayment(contractId: "{self.contract.pk}", receiptUrl: "{CBE_URL}") {{ verified message payment {{ status amount }} }} }}'
        with self.response(): result = self.graphql(query, self.owner)
        self.assertNotIn('errors', result)
        self.assertTrue(result['data']['initiateEscrowPayment']['verified'])
        second = Contract.objects.create(job_post=self.job, poster=self.owner, acceptor=self.stranger, agreed_price=100, status='ACCEPTED')
        with self.response(), self.assertRaisesRegex(ReceiptError, 'already'):
            fund_escrow(self.owner, second.pk, CBE_URL)
        self.assertEqual(EscrowPayment.objects.count(), 1)

    def test_wrong_identity_amount_status_date_or_link_never_credits(self):
        cases = [dict(creditAccountHolder='Another Person'), dict(creditAccountHolder=''), dict(creditAccountNo='1****9999'),
                 dict(amountCredited='99'), dict(amountCredited='101'), dict(status='FAILED'), dict(thirdPartyStatus='FAILED'),
                 dict(dateTimes=[(timezone.now() - timedelta(days=1)).isoformat()]),
                 dict(dateTimes=[(timezone.now() + timedelta(hours=1)).isoformat()]), dict(encodedReceipt=CBE_URL + 'x')]
        for values in cases:
            with self.subTest(values=values), self.response(cbe_payload(**values)), self.assertRaises(ReceiptError):
                fund_escrow(self.owner, self.contract.pk, CBE_URL)
        self.assertFalse(EscrowPayment.objects.exists())

    def test_missing_inactive_and_changed_config_fail_closed(self):
        self.recipient.is_active = False; self.recipient.save()
        with self.assertRaises(ReceiptError): fund_escrow(self.owner, self.contract.pk, CBE_URL)
        self.recipient.is_active = True; self.recipient.save()
        from . import payments
        original = payments.verify_receipt
        def changed(*args):
            result = original(*args)
            self.recipient.name = 'Changed'; self.recipient.save()
            return result
        with self.response(), patch('api.payments.verify_receipt', side_effect=changed), self.assertRaisesRegex(ReceiptError, 'changed'):
            fund_escrow(self.owner, self.contract.pk, CBE_URL)
        self.assertFalse(EscrowPayment.objects.exists())

    def test_unrelated_user_never_reaches_provider(self):
        with patch('api.payments.verify_receipt') as verify, self.assertRaises(ReceiptError):
            fund_escrow(self.stranger, self.contract.pk, CBE_URL)
        verify.assert_not_called()

    def test_telebirr_funding(self):
        EscrowRecipient.objects.create(provider='TELEBIRR', name='Escrow Test Account', account_number='0910001234', is_active=True)
        with patch('api.receipts.fetch_receipt', return_value=('TELEBIRR', TELE_URL, tele_payload(), 'text/html')):
            payment = fund_escrow(self.owner, self.contract.pk, TELE_URL)
        self.assertEqual(payment.payment_method, 'TELEBIRR')
        self.assertEqual(payment.amount, 100)

    def test_database_constraint_blocks_replay_even_without_service(self):
        with self.response(): payment = fund_escrow(self.owner, self.contract.pk, CBE_URL)
        with self.assertRaises(IntegrityError), transaction.atomic():
            EscrowPayment.objects.create(contract=self.contract, payer=self.owner, amount=100, payment_method='CBE', tx_ref=payment.tx_ref, status='PAID')

    def test_recipient_requires_full_valid_account(self):
        self.recipient.account_number = '1****1234'
        with self.assertRaises(ValidationError): self.recipient.save()

    def test_http_verification_is_rate_limited_before_network_access(self):
        from .payments import throttle_verification
        for _ in range(5): throttle_verification(self.owner)
        with self.assertRaisesRegex(ReceiptError, 'one minute'):
            throttle_verification(self.owner)
        throttle_verification(self.stranger)

    def test_verified_ledger_cannot_be_deleted_with_its_contract(self):
        from django.db.models.deletion import ProtectedError
        with self.response(): fund_escrow(self.owner, self.contract.pk, CBE_URL)
        with self.assertRaises(ProtectedError): self.contract.delete()
        with self.assertRaises(ProtectedError): self.owner.delete()

    def test_malformed_provider_fields_and_encoding_fail_closed(self):
        for payload in [cbe_payload(status=None), cbe_payload(dateTimes=[123]), b'null', b'\xff']:
            with self.subTest(payload=payload), self.assertRaises(ReceiptError):
                parse_receipt(payload, 'application/json', 'CBE')

    def test_admin_session_cookie_does_not_authenticate_csrf_exempt_graphql(self):
        self.client.force_login(self.owner)
        result = self.graphql('{ myJobs { id } }')
        self.assertTrue(result.get('errors'))

    def test_pagination_rejects_unbounded_requests(self):
        for args in ['limit: 1000', 'limit: 0', 'offset: -1']:
            with self.subTest(args=args):
                self.assertTrue(self.graphql('{ availableJobs(' + args + ') { id } }').get('errors'))

    def test_query_alias_and_expanded_fragment_budgets(self):
        aliases = ' '.join(f'job{i}: allJobs {{ id }}' for i in range(101))
        self.assertTrue(self.graphql('{' + aliases + '}').get('errors'))
        fragments = ' '.join('...Many' for _ in range(80))
        selections = ' '.join(f'field{i}: title' for i in range(15))
        query = '{ allJobs { ' + fragments + ' } } fragment Many on JobPostingType { ' + selections + ' }'
        self.assertTrue(self.graphql(query).get('errors'))

    def test_config_is_authenticated_read_only_and_contains_no_sample_accounts(self):
        self.assertTrue(self.graphql('{ escrowRecipients { accountNumber } }').get('errors'))
        result = self.graphql('{ escrowRecipients { provider accountNumber } }', self.owner)
        self.assertEqual(result['data']['escrowRecipients'][0]['accountNumber'], '1000000001234')
        self.assertFalse(self.client.login(username=self.owner.username, password='wrong'))
