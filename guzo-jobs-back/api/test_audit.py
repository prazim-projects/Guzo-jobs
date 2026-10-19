"""Audit gates assert desired protections; known defects deliberately fail."""
import base64
from datetime import timedelta
from decimal import Decimal
import json
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from graphql_jwt.shortcuts import get_token

from .models import Contract, EscrowPayment, JobPosting, Notification, UserProfile
from .mutation import InitiateEscrowPayment, confirmJobCompleted
from .utils import validate_product_image
from guzo_jobs_backend.schema import schema


class AuditFixture(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = UserProfile.objects.create_user(username='audit-owner', phone_number='+251900000001', email='owner@example.invalid')
        cls.worker = UserProfile.objects.create_user(username='audit-worker', phone_number='+251900000002', email='worker@example.invalid')
        cls.stranger = UserProfile.objects.create_user(username='audit-stranger', phone_number='+251900000003')
        cls.job = JobPosting.objects.create(user=cls.owner, title='Audit parcel', description='Synthetic fixture',
            expires_at=timezone.now() + timedelta(days=1), origin='Addis', destination='Adama', price=100)
        cls.contract = Contract.objects.create(job_post=cls.job, poster=cls.owner, acceptor=cls.worker,
            agreed_price=100, status=Contract.Status.PENDING)

    def graphql(self, query, user=None, token=None):
        if user is not None:
            token = get_token(user)
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'} if token else {}
        response = self.client.post('/graphql/', data=json.dumps({'query': query}), content_type='application/json', **headers)
        self.assertIn(response.status_code, (200, 400))
        return response.json()

    def info(self, user):
        return SimpleNamespace(context=SimpleNamespace(user=user))


class SecurityAuditTests(AuditFixture):
    def test_anonymous_users_cannot_enumerate_private_contact_details(self):
        result = self.graphql('{ allUsers { id email phoneNumber } }')
        self.assertTrue(result.get('errors') or not result.get('data', {}).get('allUsers'), 'Anonymous allUsers exposes private email/phone data')

    def test_other_users_cannot_read_private_contacts_by_id(self):
        result = self.graphql(f'{{ userById(id: "{self.owner.pk}") {{ email phoneNumber }} }}', self.stranger)
        exposed = (result.get('data') or {}).get('userById') or {}
        self.assertFalse(exposed.get('email') or exposed.get('phoneNumber'), 'Arbitrary userById returns another account contact information')

    def test_anonymous_users_cannot_read_escrow_receipts(self):
        EscrowPayment.objects.create(contract=self.contract, payer=self.owner, amount=100, payment_method='TELEBIRR',
            tx_ref='PRIVATE-REF', receipt_url='https://example.invalid/private-receipt', status='PAID')
        result = self.graphql('{ allJobs { contracts { escrowPayments { txRef receiptUrl amount } } } }')
        receipts = [payment for job in (result.get('data') or {}).get('allJobs', []) or []
                    for contract in job.get('contracts', []) or [] for payment in contract.get('escrowPayments', []) or []]
        self.assertFalse(receipts, 'Public allJobs exposes private payment references and receipt URLs')

    def test_unrelated_user_cannot_delete_pending_application(self):
        result = self.graphql(f'mutation {{ rejectJobApplication(contractId: "{self.contract.pk}") {{ success }} }}', self.stranger)
        self.assertTrue(Contract.objects.filter(pk=self.contract.pk).exists(), 'Unrelated authenticated user deleted another contract')
        self.assertTrue(result.get('errors'))

    def test_applicant_cannot_bypass_owner_approval_by_setting_status(self):
        Contract.objects.all().delete()
        result = self.graphql(f'mutation {{ acceptJobPost(jobPostId: "{self.job.pk}", status: "ACCEPTED") {{ contract {{ id status }} }} }}', self.worker)
        self.assertFalse(Contract.objects.filter(status='ACCEPTED').exists(), 'Applicant directly created an ACCEPTED contract')
        self.assertTrue(result.get('errors') or Contract.objects.filter(status='PENDING').exists())

    def test_expired_bearer_token_is_rejected(self):
        token = get_token(self.owner, exp=1)
        result = self.graphql('{ myJobs { id } }', token=token)
        self.assertTrue(result.get('errors'), 'Signed token with exp=1 still authenticates')

    def test_private_queries_require_authentication(self):
        for field in ['myJobs { id }', 'myNotifications { id }', 'mySupportTickets { id }', 'myTransactionSummary { totalPaid }']:
            with self.subTest(field=field):
                self.assertTrue(self.graphql('{ ' + field + ' }').get('errors'))

    def test_non_owner_cannot_fund_escrow(self):
        self.contract.status = 'ACCEPTED'; self.contract.save()
        result = InitiateEscrowPayment.mutate(None, self.info(self.stranger), self.contract.pk, 'https://example.invalid/receipt')
        self.assertFalse(result.verified)
        self.assertIn('Only the job poster', result.message)
        self.assertEqual(EscrowPayment.objects.count(), 0)

    def test_non_recipient_cannot_mark_notification_read(self):
        note = Notification.objects.create(recipient=self.owner, type='JOB_ACCEPTED', title='Private', message='Private')
        result = self.graphql(f'mutation {{ markNotificationRead(notificationId: "{note.pk}") {{ notification {{ id }} }} }}', self.stranger)
        note.refresh_from_db()
        self.assertTrue(result.get('errors')); self.assertFalse(note.is_read)

    def test_query_depth_is_bounded(self):
        nested = 'id'
        for _ in range(12):
            nested = 'id contracts { jobPost { ' + nested + ' } }'
        result = self.graphql('{ allJobs { ' + nested + ' } }')
        self.assertTrue(result.get('errors'), 'GraphQL accepted 25+ levels of recursive job/contract selections')

    def test_receipt_must_contain_receiver_identity(self):
        from .receipts import parse_receipt, ReceiptError
        with self.assertRaises(ReceiptError):
            parse_receipt(b'{"status":"COMPLETED","amountCredited":"100"}', 'application/json', 'CBE')

    def test_untrusted_receipt_host_is_rejected_before_network_access(self):
        from .receipts import fetch_receipt, ReceiptError
        with patch('api.receipts.socket.getaddrinfo') as dns:
            for url in ['http://127.0.0.1/admin', 'https://transactioninfo.ethiotelecom.et.evil.invalid/receipt/x', 'file:///etc/passwd']:
                with self.subTest(url=url), self.assertRaises(ReceiptError):
                    fetch_receipt(url)
            dns.assert_not_called()

    def test_receipt_reference_cannot_fund_two_contracts(self):
        from .models import EscrowRecipient
        from .receipts import Receipt
        EscrowRecipient.objects.create(provider='CBE', name='Test Escrow', account_number='1000000001234', is_active=True)
        self.contract.status = 'ACCEPTED'; self.contract.save()
        second = Contract.objects.create(job_post=self.job, poster=self.owner, acceptor=self.stranger, agreed_price=100, status='ACCEPTED')
        url = 'https://mbreciept.cbe.com.et/v2-SYNTHETIC12345'
        receipt = Receipt('CBE', 'SAME123456', 'Test Escrow', '1****1234', Decimal('100'), timezone.now(), 'COMPLETED')
        with patch('api.payments.verify_receipt', return_value=(receipt, url)):
            first = InitiateEscrowPayment.mutate(None, self.info(self.owner), self.contract.pk, url)
            self.assertTrue(first.verified)
            replay = InitiateEscrowPayment.mutate(None, self.info(self.owner), second.pk, url)
            self.assertFalse(replay.verified)
        self.assertEqual(EscrowPayment.objects.filter(tx_ref='SAME123456', status='PAID').count(), 1)

    def test_fayda_complete_rejects_non_object_json_without_server_error(self):
        for payload in ['[]', 'null', '"ticket"']:
            with self.subTest(payload=payload):
                response = self.client.post('/auth/fayda/complete/', data=payload, content_type='application/json')
                self.assertEqual(response.status_code, 400)

    def test_upload_rejects_svg_disguised_as_image(self):
        payload = 'data:image/svg+xml;base64,' + base64.b64encode(b'<svg onload="alert(1)"/>').decode()
        with self.assertRaisesRegex(Exception, 'Unsupported image type'):
            validate_product_image(payload)


class LogicAuditTests(AuditFixture):
    def test_owner_cannot_apply_to_own_job(self):
        result = self.graphql(f'mutation {{ acceptJobPost(jobPostId: "{self.job.pk}") {{ contract {{ id }} }} }}', self.owner)
        self.assertTrue(result.get('errors')); self.assertEqual(Contract.objects.count(), 1)

    def test_duplicate_application_is_rejected(self):
        result = self.graphql(f'mutation {{ acceptJobPost(jobPostId: "{self.job.pk}") {{ contract {{ id }} }} }}', self.worker)
        self.assertTrue(result.get('errors')); self.assertEqual(Contract.objects.count(), 1)

    def test_expired_jobs_are_not_available(self):
        self.job.expires_at = timezone.now() - timedelta(seconds=1); self.job.save()
        result = self.graphql('{ availableJobs { id } }')
        self.assertNotIn(str(self.job.pk), [job['id'] for job in result['data']['availableJobs']])

    def test_expired_jobs_cannot_receive_new_applications(self):
        self.job.expires_at = timezone.now() - timedelta(days=1); self.job.save()
        result = self.graphql(f'mutation {{ acceptJobPost(jobPostId: "{self.job.pk}") {{ contract {{ id }} }} }}', self.stranger)
        self.assertTrue(result.get('errors'), 'Expired job accepted a new application')

    def test_partially_completed_jobs_are_not_available(self):
        self.contract.status = 'COMPLETED_BY_POSTER'; self.contract.save()
        result = self.graphql('{ availableJobs { id } }')
        self.assertNotIn(str(self.job.pk), [job['id'] for job in result['data']['availableJobs']])

    def test_completion_requires_funded_escrow(self):
        self.contract.status = 'ACCEPTED'; self.contract.save()
        with self.assertRaisesRegex(Exception, 'Escrow must be paid'):
            confirmJobCompleted.mutate(None, self.info(self.owner), self.contract.pk)

    def test_both_parties_must_confirm_before_manual_payout(self):
        self.contract.status = 'ACCEPTED'; self.contract.save()
        payment = EscrowPayment.objects.create(contract=self.contract, payer=self.owner, amount=100,
            payment_method='TELEBIRR', tx_ref='AUDIT-PAID', status='PAID')
        confirmJobCompleted.mutate(None, self.info(self.worker), self.contract.pk)
        payment.refresh_from_db(); self.assertEqual(payment.status, 'PAID')
        with self.assertRaisesRegex(Exception, 'Only the job poster'):
            confirmJobCompleted.mutate(None, self.info(self.worker), self.contract.pk)
        confirmJobCompleted.mutate(None, self.info(self.owner), self.contract.pk)
        self.contract.refresh_from_db(); payment.refresh_from_db()
        self.assertEqual(self.contract.status, 'COMPLETED'); self.assertEqual(payment.status, 'PAID')
        self.assertIn('manual payout', Notification.objects.latest('id').message)

    def test_job_creation_rejects_invalid_type_and_past_expiry(self):
        result = self.graphql('mutation { createJobPost(title: "Audit", description: "Audit", origin: "A", destination: "B", postType: "INVALID", price: 10, expiresAt: "2020-01-01T00:00:00Z") { jobPost { id } } }', self.owner)
        self.assertTrue(result.get('errors'), 'Mutation accepted an invalid job type and expiry in the past')


class PerformanceAuditTests(AuditFixture):
    def test_local_schema_latency_stays_within_smoke_budget(self):
        query = '{ availableJobs { id title user { id } contracts { id acceptor { id } } } }'
        timings = []
        for index in range(35):
            started = time.perf_counter()
            result = schema.execute(query, context_value=SimpleNamespace(user=self.owner))
            self.assertIsNone(result.errors)
            if index >= 5:
                timings.append((time.perf_counter() - started) * 1000)
        timings.sort()
        metrics = {'samples': 30, 'warmup': 5, 'p50Ms': timings[14], 'p95Ms': timings[28],
                   'p50BudgetMs': 100, 'p95BudgetMs': 250,
                   'note': 'Serial local schema executions over one synthetic job in SQLite; excludes HTTP, TLS, provider calls and concurrency.'}
        output = Path(__file__).resolve().parents[2] / 'docs' / 'audit' / 'results'
        output.mkdir(parents=True, exist_ok=True)
        (output / 'latency.json').write_text(json.dumps(metrics, indent=2))
        self.assertLess(metrics['p50Ms'], 100)
        self.assertLess(metrics['p95Ms'], 250)

    def test_feed_query_count_remains_bounded_as_data_grows(self):
        query = '{ allJobs { id user { id faydaLinked } contracts { id poster { id } acceptor { id } escrowPayments { id } } } }'
        def measure():
            with CaptureQueriesContext(connection) as captured:
                result = schema.execute(query, context_value=SimpleNamespace(user=AnonymousUser()))
                self.assertIsNone(result.errors)
            return len(captured)
        small = measure()
        jobs = JobPosting.objects.bulk_create([JobPosting(user=self.owner, title=f'Audit job {i}', description='fixture',
            expires_at=timezone.now() + timedelta(days=1), price=100) for i in range(19)])
        Contract.objects.bulk_create([Contract(job_post=job, poster=self.owner, acceptor=self.worker, agreed_price=100) for job in jobs])
        large = measure()
        output = Path(__file__).resolve().parents[2] / 'docs' / 'audit' / 'results'
        output.mkdir(parents=True, exist_ok=True)
        (output / 'query-benchmark.json').write_text(json.dumps({'jobs1': small, 'jobs20': large, 'maxQueries': 8, 'maxGrowth': 2}, indent=2))
        self.assertLessEqual(large, 8, f'20 jobs require {large} SQL queries (1 job: {small}); budget 8')
        self.assertLessEqual(large - small, 2)

    def test_feed_has_server_side_pagination(self):
        field = schema.graphql_schema.query_type.fields['availableJobs']
        self.assertTrue({'first', 'limit', 'page', 'offset'} & set(field.args), 'availableJobs has no server-side pagination arguments')
