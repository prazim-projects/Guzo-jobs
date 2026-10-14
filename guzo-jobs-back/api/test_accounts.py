from types import SimpleNamespace
from urllib.parse import urlparse, parse_qs

from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.test import TestCase, override_settings
from graphql import GraphQLError

from .account import DeleteAccount, RequestPasswordReset, ResetPassword
from .models import UserProfile, JobPosting, Contract
from .mutation import RegisterUser
from django.utils import timezone


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   PASSWORD_RESET_URL='https://example.com/#/reset-password')
class AccountTests(TestCase):
    password = 'W7!mQ9#vL2@xR8kP'

    def setUp(self):
        self.user = UserProfile.objects.create_user(username='traveler', phone_number='+251900000001',
                                                    email='traveler@example.com', password=self.password)
        self.info = SimpleNamespace(context=SimpleNamespace(user=self.user))

    def test_registration_rejects_mismatch_and_weak_password(self):
        for password, confirmation, expected in [('short', 'short', 'weak_password'),
                                                  (self.password, 'different', 'password_mismatch')]:
            with self.assertRaisesRegex(GraphQLError, expected):
                RegisterUser.mutate(None, self.info, 'newuser', password, '+251900000002', confirmation)
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_reset_link_changes_password_and_cannot_be_reused(self):
        RequestPasswordReset.mutate(None, self.info, self.user.email)
        self.assertEqual(len(mail.outbox), 1)
        link = mail.outbox[0].body.splitlines()[1]
        query = parse_qs(urlparse(link).fragment.split('?', 1)[1])
        new_password = 'Z8@hT6!pM4#rV2sK'
        args = (None, self.info, query['uid'][0], query['token'][0], new_password, new_password)
        ResetPassword.mutate(*args)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertFalse(self.user.check_password(self.password))
        with self.assertRaisesRegex(GraphQLError, 'invalid_reset'):
            ResetPassword.mutate(*args)

    def test_unknown_email_has_same_success_response(self):
        self.assertTrue(RequestPasswordReset.mutate(None, self.info, 'missing@example.com').success)
        self.assertEqual(len(mail.outbox), 0)

    def test_delete_requires_current_password_and_authentication(self):
        with self.assertRaisesRegex(GraphQLError, 'invalid_credentials'):
            DeleteAccount.mutate(None, self.info, 'incorrect')
        anonymous = SimpleNamespace(context=SimpleNamespace(user=AnonymousUser()))
        with self.assertRaisesRegex(GraphQLError, 'invalid_credentials'):
            DeleteAccount.mutate(None, anonymous, self.password)
        self.assertTrue(UserProfile.objects.filter(pk=self.user.pk).exists())
        DeleteAccount.mutate(None, self.info, self.password)
        self.assertEqual(UserProfile.objects.count(), 0)

    def test_delete_blocks_active_contract(self):
        other = UserProfile.objects.create_user(username='other', phone_number='+251900000002')
        job = JobPosting.objects.create(user=self.user, title='Delivery', expires_at=timezone.now())
        Contract.objects.create(job_post=job, poster=self.user, acceptor=other,
                                agreed_price=100, status=Contract.Status.ACCEPTED)
        with self.assertRaisesRegex(GraphQLError, 'active_contracts'):
            DeleteAccount.mutate(None, self.info, self.password)
        self.assertTrue(UserProfile.objects.filter(pk=self.user.pk).exists())
