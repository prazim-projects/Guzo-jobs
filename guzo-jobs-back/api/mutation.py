import graphql_jwt
import graphene
from django.contrib.auth import get_user_model
from graphql_jwt.shortcuts import create_refresh_token, get_token

from .types import UserType, JobPostingType
from .models import *

class RegisterUser(graphene.Mutation):
    user = graphene.Field(UserType)
    token = graphene.String()
    refresh_token = graphene.String()

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        phone_number = graphene.String(required=True)

    @classmethod
    def mutate(cls, root, info, username, password, phone_number):
        User = get_user_model()
        user = User(username=username, phone_number=phone_number)
        user.set_password(password)
        user.save()
        token = get_token(user)
        refresh_token = create_refresh_token(user)

        return RegisterUser(user=user, token=token, refresh_token=refresh_token)

class createJobPost(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=True)
        expires_at = graphene.DateTime(required=True)
        origin = graphene.String(required=True)
        destination = graphene.String(required=True)
        post_type = graphene.String(required=True)

    jobPost = graphene.Field(JobPostingType)

    @classmethod
    def mutate(cls, root, info, title, description, expires_at, origin, destination, post_type):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("you must be logged in to create a job post.")

        jobPost = JobPosting(
            title=title,
            description=description,
            expires_at=expires_at,
            user=user,
            origin=origin,
            destination=destination,
            post_type=post_type
        )
        jobPost.save()
        return createJobPost(jobPost=jobPost)

class ObtainJSONWebToken(graphql_jwt.JSONWebTokenMutation):
    user = graphene.Field(UserType)

    @classmethod
    def resolve(cls, root, info, **kwargs):
        return cls(user=info.context.user)

class Mutation(graphene.ObjectType):
    token_auth = ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

    RegisterUser = RegisterUser.Field()
    createJobPost = createJobPost.Field()