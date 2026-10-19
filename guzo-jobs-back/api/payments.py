from django.db import transaction, IntegrityError
from django.utils import timezone
from datetime import timedelta

from .models import Contract, EscrowPayment, EscrowRecipient, Notification, ReceiptVerificationAttempt, UserProfile
from .receipts import ReceiptError, receipt_url, verify_receipt


def throttle_verification(user):
    if not user.is_authenticated:
        raise ReceiptError('You must be logged in to fund escrow.')
    with transaction.atomic():
        UserProfile.objects.select_for_update().get(pk=user.pk)
        cutoff = timezone.now() - timedelta(minutes=1)
        attempts = ReceiptVerificationAttempt.objects.filter(user=user)
        if attempts.filter(created_at__gte=cutoff).count() >= 5:
            raise ReceiptError('Too many verification attempts. Please wait one minute and retry.')
        attempts.filter(created_at__lt=cutoff).delete()
        ReceiptVerificationAttempt.objects.create(user=user)


def fund_escrow(user, contract_id, url):
    if not user.is_authenticated:
        raise ReceiptError('You must be logged in to fund escrow.')
    contract = Contract.objects.get(pk=contract_id)
    if contract.poster_id != user.pk:
        raise ReceiptError('Only the job poster can fund escrow.')
    if contract.status != Contract.Status.ACCEPTED:
        raise ReceiptError('Escrow can only be funded after acceptance.')
    provider, _ = receipt_url(url)
    try:
        recipient = EscrowRecipient.objects.get(provider=provider, is_active=True)
    except EscrowRecipient.DoesNotExist:
        raise ReceiptError('This escrow receiving account is not configured. Contact support.') from None
    # Network IO is outside the write transaction; re-check all mutable state before crediting.
    receipt, canonical = verify_receipt(url, recipient, contract.agreed_price, contract.created_at)
    try:
        with transaction.atomic():
            locked = Contract.objects.select_for_update().get(pk=contract_id)
            current = EscrowRecipient.objects.select_for_update().get(pk=recipient.pk)
            if not current.is_active or current.updated_at != recipient.updated_at:
                raise ReceiptError('The receiving account changed. Refresh the payment instructions and retry.')
            if locked.poster_id != user.pk or locked.status != Contract.Status.ACCEPTED or locked.agreed_price != receipt.amount:
                raise ReceiptError('The contract changed. Refresh the page and retry.')
            existing = EscrowPayment.objects.filter(contract=locked, status__in=['PAID', 'RELEASED', 'REFUNDED']).first()
            if existing:
                if existing.payment_method == provider and existing.tx_ref == receipt.reference and existing.status == 'PAID':
                    return existing
                raise ReceiptError('This contract already has a verified payment.')
            payment = EscrowPayment.objects.create(contract=locked, payer=user, amount=locked.agreed_price,
                payment_method=provider, tx_ref=receipt.reference, receipt_url=canonical, status='PAID',
                recipient=current, verified_at=timezone.now(), verification_note='Verified directly with the receipt provider.',
                verification_snapshot={'recipient_name': current.name, 'recipient_account': current.account_number,
                    'receipt_account': receipt.recipient_account, 'account_match': 'masked' if '*' in receipt.recipient_account else 'full',
                    'paid_at': receipt.paid_at.isoformat(), 'amount': str(receipt.amount), 'sha256': receipt.digest})
            Notification.objects.create(recipient=locked.acceptor, actor=user, contract=locked, type='ESCROW_PAID',
                title='Escrow funded', message=f'Escrow funding for "{locked.job_post.title}" has been verified via {provider}.')
            return payment
    except IntegrityError:
        # A database constraint is the final authority even when requests race.
        raise ReceiptError('This receipt or contract already has a verified payment.') from None
