import graphql_jwt
import graphene
from django.contrib.auth import get_user_model
from graphql_jwt.shortcuts import create_refresh_token, get_token

from .types import UserType, JobPostingType, ContractType
from .models import *


class editProfile(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        email = graphene.String(required=False)
        phone_number = graphene.String(required=False)
        bio = graphene.String(required=False)
        profile_picture = graphene.String(required=False)

    @classmethod
    def mutate(cls, root, info, email=None, phone_number=None, bio=None, profile_picture=None):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to edit your profile.")

        if email is not None:
            user.email = email
        if phone_number is not None:
            user.phone_number = phone_number
        if bio is not None:
            user.bio = bio
        if profile_picture is not None:
            user.profile_picture = profile_picture

        user.save()
        return editProfile(user=user)
    

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
        # print(f"DEBUG: Auth Header -> {info.context.META.get('HTTP_AUTHORIZATION')}")
        # print(f"DEBUG: User in Context -> {info.context.user}")

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
    

class acceptJobPost(graphene.Mutation):
    class Arguments:
        job_post_id = graphene.ID(required=True) 
        status = graphene.String(required=False)      

    contract = graphene.Field(lambda: ContractType)

    @classmethod
    def mutate(cls, root, info, job_post_id, status):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to Interact with job post.")
       
        try:
            job_post = JobPosting.objects.get(pk=job_post_id)
        except JobPosting.DoesNotExist:
            raise Exception("Job post not found.")

        if job_post.user == user:
            raise Exception("You cannot accept your own job post")

        if hasattr(job_post, 'contract'):
            raise Exception("This job post has already been accepted.")

        contract = Contract(
            job_post=job_post,
            poster=job_post.user,
            acceptor=user,
            status=status if status else Contract.Status.PENDING,
            agreed_price=job_post.price if job_post.price else 0.0
        )
        contract.save()
        return acceptJobPost(contract=contract)
    

class ConfirmJobAcceptance(graphene.Mutation):
    class Arguments:
        poster = graphene.ID(required=True)
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    @classmethod
    def mutate(cls, root, info, id, poster):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to confirm job acceptance.")

        try:
            job_post = JobPosting.objects.get(pk=id)
        except JobPosting.DoesNotExist:
            raise Exception("Job post not found.")

        if job_post.user.id != int(poster):
            raise Exception("Only the job owner can confirm acceptance.")

        try:
            contract = Contract.objects.get(job_post=job_post)
        except Contract.DoesNotExist:
            raise Exception("No contract found for this job post.")

        contract.status = Contract.Status.ACCEPTED
        contract.save()
        return ConfirmJobAcceptance(success=True)

class confirmJobCompleted(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    @classmethod
    def mutate(cls, root, info, id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to confirm job completion.")

        try:
            job_post = JobPosting.objects.get(pk=id)
        except JobPosting.DoesNotExist:
            raise Exception("Job post not found.")

        try:
            contract = Contract.objects.get(job_post=job_post)
        except Contract.DoesNotExist:
            raise Exception("No contract found for this job post.")

        if contract.acceptor != user:
            raise Exception("Only the acceptor can confirm completion.")

        contract.status = Contract.Status.COMPLETED
        contract.save()
        return confirmJobCompleted(success=True)
    
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
    editProfile = editProfile.Field()
    acceptJobPost = acceptJobPost.Field()
    confirmJobContract = ConfirmJobAcceptance.Field()
    confirmJobCompleted = confirmJobCompleted.Field()