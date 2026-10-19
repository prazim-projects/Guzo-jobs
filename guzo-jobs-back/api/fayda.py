import base64
import hashlib
import json
import os
import secrets
from datetime import timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import jwt
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from graphql_jwt.shortcuts import get_token

from .models import FaydaAuthAttempt, FaydaIdentity, UserProfile


ASSERTION_TYPE = 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'


def _setting(name):
    return getattr(settings, name, '') or os.environ.get(name, '')


def _configured():
    return all(_setting(name) for name in (
        'FAYDA_CLIENT_ID', 'FAYDA_PRIVATE_KEY_BASE64', 'FAYDA_AUTHORIZATION_ENDPOINT',
        'FAYDA_TOKEN_ENDPOINT', 'FAYDA_USERINFO_ENDPOINT', 'FAYDA_JWKS_URI',
        'FAYDA_ISSUER', 'FAYDA_REDIRECT_URI', 'FAYDA_FRONTEND_URL',
    ))


def _browser_destination(platform, **params):
    query = urlencode(params)
    if platform == 'android':
        return f'{_setting("FAYDA_ANDROID_REDIRECT") or "guzojobs://auth/fayda"}?{query}'
    return f'{_setting("FAYDA_FRONTEND_URL").rstrip("/")}/#/fayda/callback?{query}'


def _no_store(response):
    response['Cache-Control'] = 'no-store'
    response['Referrer-Policy'] = 'no-referrer'
    return response


def _post_form(url, fields):
    request = Request(url, data=urlencode(fields).encode(), headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
    })
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read(1_000_000))


def _client_assertion():
    key_data = json.loads(base64.b64decode(_setting('FAYDA_PRIVATE_KEY_BASE64')))
    if 'keys' in key_data:
        key_data = key_data['keys'][0]
    key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_data))
    now = int(timezone.now().timestamp())
    return jwt.encode({
        'iss': _setting('FAYDA_CLIENT_ID'),
        'sub': _setting('FAYDA_CLIENT_ID'),
        'aud': _setting('FAYDA_TOKEN_ENDPOINT'),
        'iat': now,
        'exp': now + 300,
        'jti': secrets.token_urlsafe(24),
    }, key, algorithm='RS256', headers={'kid': key_data.get('kid', '')})


def _verified_claims(token):
    signing_key = jwt.PyJWKClient(_setting('FAYDA_JWKS_URI'), timeout=10).get_signing_key_from_jwt(token)
    return jwt.decode(
        token, signing_key.key, algorithms=['RS256'],
        audience=_setting('FAYDA_CLIENT_ID'), issuer=_setting('FAYDA_ISSUER'),
        options={'require': ['exp', 'iss', 'aud', 'sub']},
    )


def _verified_identity(code, attempt):
    tokens = _post_form(_setting('FAYDA_TOKEN_ENDPOINT'), {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': _setting('FAYDA_REDIRECT_URI'),
        'client_id': _setting('FAYDA_CLIENT_ID'),
        'client_assertion': _client_assertion(),
        'client_assertion_type': ASSERTION_TYPE,
        'code_verifier': attempt.code_verifier,
    })
    id_claims = _verified_claims(tokens['id_token'])
    if not secrets.compare_digest(str(id_claims.get('nonce', '')), attempt.nonce):
        raise ValueError('Invalid Fayda nonce')

    request = Request(_setting('FAYDA_USERINFO_ENDPOINT'), headers={
        'Authorization': f"Bearer {tokens['access_token']}",
        'Accept': 'application/jwt',
    })
    with urlopen(request, timeout=15) as response:
        userinfo_token = response.read(1_000_000).decode().strip()
    userinfo = _verified_claims(userinfo_token)
    if not secrets.compare_digest(str(id_claims['sub']), str(userinfo['sub'])):
        raise ValueError('Fayda subject mismatch')
    return userinfo


def _account_for(claims):
    subject = str(claims['sub'])
    if len(subject) > 255:
        raise ValueError('Fayda subject is too long')
    identity = FaydaIdentity.objects.select_related('user').filter(subject=subject).first()
    if identity:
        if not identity.user.is_active:
            raise ValueError('Account is disabled')
        return identity.user

    phone = str(claims.get('phone_number') or claims.get('phone') or '').strip()
    if not phone or len(phone) > 15:
        raise ValueError('Fayda did not provide a usable phone number')
    if UserProfile.objects.filter(phone_number=phone).exists():
        raise ValueError('A local account already uses this phone number')

    with transaction.atomic():
        user = UserProfile(
            username=f'fayda_{secrets.token_hex(12)}',
            phone_number=phone,
            email=str(claims.get('email') or '')[:254],
        )
        user.set_unusable_password()
        user.save()
        FaydaIdentity.objects.create(user=user, subject=subject)
    return user


def _link_account(user, claims):
    subject = str(claims['sub'])
    if not subject or len(subject) > 255 or not user.is_active:
        raise ValueError('Invalid Fayda identity or local account')
    existing = FaydaIdentity.objects.filter(subject=subject).first()
    if existing:
        if existing.user_id != user.id:
            raise ValueError('Fayda identity is already linked')
        return user
    if FaydaIdentity.objects.filter(user=user).exists():
        raise ValueError('This account is already linked to another Fayda identity')
    FaydaIdentity.objects.create(user=user, subject=subject)
    return user


def authorization_url(platform='web', user=None):
    if not _configured():
        raise ValueError('Fayda sign-in is not configured.')
    if platform not in ('web', 'android'):
        raise ValueError('Unsupported platform')

    FaydaAuthAttempt.objects.filter(expires_at__lt=timezone.now()).delete()
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    nonce = secrets.token_urlsafe(32)
    FaydaAuthAttempt.objects.create(
        state=state, code_verifier=verifier, nonce=nonce, platform=platform,
        expires_at=timezone.now() + timedelta(minutes=5),
        user=user,
    )
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    claims = json.dumps({'userinfo': {
        'phone_number': {'essential': True},
        'name': {'essential': False},
        'email': {'essential': False},
    }, 'id_token': {}})
    params = {
        'client_id': _setting('FAYDA_CLIENT_ID'),
        'response_type': 'code',
        'redirect_uri': _setting('FAYDA_REDIRECT_URI'),
        'scope': 'openid profile email',
        'state': state,
        'nonce': nonce,
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'claims': claims,
        'claims_locales': 'en',
    }
    return f'{_setting("FAYDA_AUTHORIZATION_ENDPOINT")}?{urlencode(params)}'


@require_GET
def start(request):
    platform = 'android' if request.GET.get('platform') == 'android' else 'web'
    try:
        url = authorization_url(platform)
    except ValueError as error:
        return _no_store(HttpResponse(str(error), status=503))
    return _no_store(redirect(url))


@require_GET
def callback(request):
    state = request.GET.get('state', '')
    attempt = FaydaAuthAttempt.objects.filter(state=state, expires_at__gt=timezone.now(), ticket_hash='').first()
    if not attempt:
        return _no_store(HttpResponse('Invalid or expired Fayda request.', status=400))
    claimed = FaydaAuthAttempt.objects.filter(state=state, ticket_hash='').update(ticket_hash='processing')
    if not claimed:
        return _no_store(HttpResponse('Fayda request was already used.', status=400))

    error = request.GET.get('error')
    code = request.GET.get('code')
    if error or not code:
        attempt.delete()
        return _no_store(redirect(_browser_destination(attempt.platform, error='cancelled')))

    try:
        claims = _verified_identity(code, attempt)
        user = _link_account(attempt.user, claims) if attempt.user_id else _account_for(claims)
        ticket = secrets.token_urlsafe(32)
        attempt.ticket_hash = hashlib.sha256(ticket.encode()).hexdigest()
        attempt.user = user
        attempt.expires_at = timezone.now() + timedelta(minutes=2)
        attempt.save(update_fields=['ticket_hash', 'user', 'expires_at'])
    except (ValueError, KeyError, IntegrityError, jwt.PyJWTError, OSError, TypeError, json.JSONDecodeError):
        attempt.delete()
        return _no_store(redirect(_browser_destination(attempt.platform, error='verification_failed')))

    return _no_store(redirect(_browser_destination(attempt.platform, ticket=ticket)))


@csrf_exempt
@require_POST
def complete(request):
    if len(request.body) > 2048:
        return _no_store(JsonResponse({'error': 'Invalid ticket.'}, status=400))
    try:
        payload = json.loads(request.body)
        ticket = payload.get('ticket', '') if isinstance(payload, dict) else ''
    except (ValueError, TypeError):
        ticket = ''
    if not isinstance(ticket, str) or len(ticket) < 32:
        return _no_store(JsonResponse({'error': 'Invalid ticket.'}, status=400))

    ticket_hash = hashlib.sha256(ticket.encode()).hexdigest()
    attempt = FaydaAuthAttempt.objects.select_related('user').filter(
        ticket_hash=ticket_hash, expires_at__gt=timezone.now(), user__isnull=False,
    ).first()
    if not attempt or not attempt.user.is_active:
        return _no_store(JsonResponse({'error': 'Ticket expired or already used.'}, status=400))
    if not FaydaAuthAttempt.objects.filter(state=attempt.state, ticket_hash=ticket_hash).update(ticket_hash=''):
        return _no_store(JsonResponse({'error': 'Ticket expired or already used.'}, status=400))
    user = attempt.user
    attempt.delete()
    return _no_store(JsonResponse({
        'token': get_token(user),
        'user': {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'phoneNumber': user.phone_number,
            'profilePicture': user.profile_picture,
        },
    }))
