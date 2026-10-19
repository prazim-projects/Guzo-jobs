from datetime import timedelta
import base64
import json
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase, override_settings
from django.utils import timezone
from graphql_jwt.shortcuts import get_token

from .fayda import _client_assertion, _verified_claims
from .models import FaydaAuthAttempt, FaydaIdentity, UserProfile


@override_settings(
    FAYDA_CLIENT_ID='test-client',
    FAYDA_PRIVATE_KEY_BASE64='test-key',
    FAYDA_AUTHORIZATION_ENDPOINT='https://fayda.example/authorize',
    FAYDA_TOKEN_ENDPOINT='https://fayda.example/token',
    FAYDA_USERINFO_ENDPOINT='https://fayda.example/userinfo',
    FAYDA_JWKS_URI='https://fayda.example/jwks',
    FAYDA_ISSUER='https://fayda.example',
    FAYDA_REDIRECT_URI='https://api.example/auth/fayda/callback/',
    FAYDA_FRONTEND_URL='https://app.example',
    FAYDA_ANDROID_REDIRECT='guzojobs://auth/fayda',
)
class FaydaAuthTests(TestCase):
    def _attempt(self, state='valid-state', platform='web'):
        return FaydaAuthAttempt.objects.create(
            state=state, code_verifier='verifier', nonce='nonce', platform=platform,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

    def test_start_uses_pkce_and_registered_callback(self):
        response = self.client.get('/auth/fayda/start/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('code_challenge_method=S256', response['Location'])
        self.assertIn('redirect_uri=https%3A%2F%2Fapi.example%2Fauth%2Ffayda%2Fcallback%2F', response['Location'])
        self.assertEqual(FaydaAuthAttempt.objects.count(), 1)

    @patch('api.fayda._verified_identity')
    def test_signup_then_signin_and_ticket_cannot_be_reused(self, identity):
        identity.return_value = {'sub': 'fayda-subject', 'phone_number': '+251900000001', 'email': 'a@example.com'}
        self._attempt()
        callback = self.client.get('/auth/fayda/callback/?state=valid-state&code=code')
        self.assertEqual(callback.status_code, 302)
        ticket = callback['Location'].split('ticket=')[1]
        complete = self.client.post('/auth/fayda/complete/', data={'ticket': ticket}, content_type='application/json')
        self.assertEqual(complete.status_code, 200)
        self.assertTrue(complete.json()['token'])
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(FaydaIdentity.objects.get(subject='fayda-subject').user_id, int(complete.json()['user']['id']))
        replay = self.client.post('/auth/fayda/complete/', data={'ticket': ticket}, content_type='application/json')
        self.assertEqual(replay.status_code, 400)

        self._attempt('next-state')
        second = self.client.get('/auth/fayda/callback/?state=next-state&code=code')
        self.assertEqual(second.status_code, 302)
        self.assertEqual(UserProfile.objects.count(), 1)

    @patch('api.fayda._verified_identity')
    def test_existing_phone_does_not_take_over_local_account(self, identity):
        UserProfile.objects.create_user(username='local', phone_number='+251900000002', password='secret')
        identity.return_value = {'sub': 'other-subject', 'phone_number': '+251900000002'}
        self._attempt()
        response = self.client.get('/auth/fayda/callback/?state=valid-state&code=code')
        self.assertIn('error=verification_failed', response['Location'])
        self.assertFalse(FaydaIdentity.objects.exists())

    @patch('api.fayda._verified_identity')
    def test_logged_in_user_can_explicitly_link_existing_account(self, identity):
        user = UserProfile.objects.create_user(username='local', phone_number='+251900000003', password='secret')
        begin = self.client.post(
            '/graphql/',
            data=json.dumps({'query': 'mutation { beginFaydaLink(platform: "web") { authorizationUrl } }'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {get_token(user)}',
        )
        self.assertNotIn('errors', begin.json())
        auth_url = begin.json()['data']['beginFaydaLink']['authorizationUrl']
        state = FaydaAuthAttempt.objects.get(user=user).state
        self.assertIn(state, auth_url)
        identity.return_value = {'sub': 'linked-subject', 'phone_number': '+251900000003'}
        response = self.client.get(f'/auth/fayda/callback/?state={state}&code=code')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FaydaIdentity.objects.get(subject='linked-subject').user, user)
        self.assertEqual(UserProfile.objects.count(), 1)

    def test_unknown_state_is_rejected(self):
        response = self.client.get('/auth/fayda/callback/?state=unknown&code=code')
        self.assertEqual(response.status_code, 400)

    def test_id_token_checks_signature_issuer_and_audience(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        claims = {
            'sub': 'subject', 'iss': 'https://fayda.example', 'aud': 'test-client',
            'exp': int((timezone.now() + timedelta(minutes=5)).timestamp()),
        }
        with patch('api.fayda.jwt.PyJWKClient') as jwks:
            jwks.return_value.get_signing_key_from_jwt.return_value = SimpleNamespace(key=private_key.public_key())
            valid = jwt.encode(claims, private_key, algorithm='RS256')
            self.assertEqual(_verified_claims(valid)['sub'], 'subject')
            wrong_audience = jwt.encode({**claims, 'aud': 'another-client'}, private_key, algorithm='RS256')
            with self.assertRaises(jwt.InvalidAudienceError):
                _verified_claims(wrong_audience)
            wrong_issuer = jwt.encode({**claims, 'iss': 'https://other.example'}, private_key, algorithm='RS256')
            with self.assertRaises(jwt.InvalidIssuerError):
                _verified_claims(wrong_issuer)

    def test_client_assertion_is_signed_for_token_endpoint(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        jwk = jwt.algorithms.RSAAlgorithm.to_jwk(private_key, as_dict=True)
        encoded_key = base64.b64encode(json.dumps(jwk).encode()).decode()
        with override_settings(FAYDA_PRIVATE_KEY_BASE64=encoded_key):
            assertion = _client_assertion()
        claims = jwt.decode(
            assertion, private_key.public_key(), algorithms=['RS256'],
            audience='https://fayda.example/token',
        )
        self.assertEqual(claims['iss'], 'test-client')
        self.assertEqual(claims['sub'], 'test-client')
