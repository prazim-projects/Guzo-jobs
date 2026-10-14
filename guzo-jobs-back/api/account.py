import re
from urllib.parse import urlencode

import graphene
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from graphql import GraphQLError


def validate_strong_password(password, user=None):
    if (len(password) < 12 or not re.search(r'[a-z]', password)
            or not re.search(r'[A-Z]', password) or not re.search(r'[0-9]', password)
            or not re.search(r'[^A-Za-z0-9\s]', password)):
        raise GraphQLError('weak_password')
    try:
        validate_password(password, user)
    except ValidationError:
        raise GraphQLError('weak_password')


class RequestPasswordReset(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, email):
        for user in get_user_model().objects.filter(email__iexact=email.strip(), is_active=True):
            if not user.has_usable_password():
                continue
            query = urlencode({'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                               'token': default_token_generator.make_token(user)})
            link = f'{settings.PASSWORD_RESET_URL}?{query}'
            send_mail('Guzo Jobs password reset',
                      f'Reset your password using this link:\n{link}\n\nIf you did not request this, ignore this email.',
                      settings.DEFAULT_FROM_EMAIL, [user.email])
        return cls(success=True)


class ResetPassword(graphene.Mutation):
    class Arguments:
        uid = graphene.String(required=True)
        token = graphene.String(required=True)
        password = graphene.String(required=True)
        confirm_password = graphene.String(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, uid, token, password, confirm_password):
        try:
            user = get_user_model().objects.get(pk=force_str(urlsafe_base64_decode(uid)), is_active=True)
        except (ValueError, TypeError, OverflowError, UnicodeDecodeError, get_user_model().DoesNotExist):
            raise GraphQLError('invalid_reset')
        if not default_token_generator.check_token(user, token):
            raise GraphQLError('invalid_reset')
        if password != confirm_password:
            raise GraphQLError('password_mismatch')
        validate_strong_password(password, user)
        user.set_password(password)
        user.save(update_fields=['password'])
        return cls(success=True)


class DeleteAccount(graphene.Mutation):
    class Arguments:
        password = graphene.String(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, password):
        from .models import Contract, EscrowPayment
        user = info.context.user
        if not user.is_authenticated or not user.check_password(password):
            raise GraphQLError('invalid_credentials')
        contracts = Contract.objects.filter(Q(poster=user) | Q(acceptor=user))
        if contracts.exclude(status__in=['PENDING', 'COMPLETED', 'CANCELLED']).exists() or EscrowPayment.objects.filter(contract__in=contracts, status='PAID').exists():
            raise GraphQLError('active_contracts')
        user.delete()
        return cls(success=True)
