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
        price = graphene.String(required=True)

    jobPost = graphene.Field(JobPostingType)

    @classmethod
    def mutate(cls, root, info, title, description, expires_at, origin, destination, post_type, price):
        # print(f"DEBUG: Auth Header -> {info.context.META.get('HTTP_AUTHORIZATION')}")
        # print(f"DEBUG: User in Context -> {info.context.user}")

        user = info.context.user
        if user.is_anonymous:
            raise Exception("you must be logged in to create a job post.")

        if (price < 0):
            raise Exception("Money can't be less than 0 birr")

        jobPost = JobPosting(
            title=title,
            description=description,
            expires_at=expires_at,
            user=user,
            origin=origin,
            destination=destination,
            post_type=post_type,
            price=price
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

        existing_application = Contract.objects.filter(
            job_post=job_post, 
            acceptor=user, 
            status__in=[Contract.Status.PENDING, Contract.Status.ACCEPTED]
        ).first()
        
        if existing_application:
            raise Exception("You have already applied for this job.")

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
        contract_id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    @classmethod
    def mutate(cls, root, info, contract_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to confirm job acceptance.")

        try:
            contract = Contract.objects.get(pk=contract_id)
        except Contract.DoesNotExist:
            raise Exception("Contract not found.")

        if contract.poster != user:
            raise Exception("Only the job owner can confirm acceptance.")

        if contract.status != Contract.Status.PENDING:
            raise Exception("This contract is not in pending status.")

        # Accept this contract
        contract.status = Contract.Status.ACCEPTED
        contract.save()

        # Reject all other pending contracts for this job
        Contract.objects.filter(
            job_post=contract.job_post,
            status=Contract.Status.PENDING
        ).exclude(pk=contract_id).update(status=Contract.Status.CANCELLED)

        return ConfirmJobAcceptance(success=True)

class RejectJobApplication(graphene.Mutation):
    class Arguments:
        contract_id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    @classmethod
    def mutate(cls, root, info, contract_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to reject job application.")

        try:
            contract = Contract.objects.get(pk=contract_id)
        except Contract.DoesNotExist:
            raise Exception("Contract not found.")

        if contract.status != Contract.Status.PENDING:
            raise Exception("This contract is not in pending status.")

        # Delete contract to make job available again
        contract.delete()

        return RejectJobApplication(success=True)

class confirmJobCompleted(graphene.Mutation):
    class Arguments:
        contract_id = graphene.ID(required=True)

    success = graphene.Boolean()
    
    @classmethod
    def mutate(cls, root, info, contract_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("You must be logged in to confirm job completion.")

        try:
            contract = Contract.objects.get(pk=contract_id)
        except Contract.DoesNotExist:
            raise Exception("Contract not found.")

        # Check if user is either the acceptor or the poster
        if contract.acceptor != user and contract.poster != user:
            raise Exception("Only contract parties can confirm completion.")

        # Handle different completion scenarios
        if contract.status == Contract.Status.ACCEPTED:
            # Either party can initiate completion
            if contract.acceptor == user:
                contract.status = Contract.Status.COMPLETED_BY_ACCEPTOR
            elif contract.poster == user:
                contract.status = Contract.Status.COMPLETED_BY_POSTER
            contract.save()
            return confirmJobCompleted(success=True)
            
        elif contract.status == Contract.Status.COMPLETED_BY_ACCEPTOR:
            # Only poster can confirm acceptor's completion
            if contract.poster != user:
                raise Exception("Only the job poster can confirm completion initiated by the acceptor.")
            contract.status = Contract.Status.COMPLETED
            contract.save()
            return confirmJobCompleted(success=True)
            
        elif contract.status == Contract.Status.COMPLETED_BY_POSTER:
            # Only acceptor can confirm poster's completion
            if contract.acceptor != user:
                raise Exception("Only the job acceptor can confirm completion initiated by the poster.")
            contract.status = Contract.Status.COMPLETED
            contract.save()
            return confirmJobCompleted(success=True)
            
        else:
            raise Exception("Contract is not in a state that allows completion confirmation.")
    
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
    rejectJobApplication = RejectJobApplication.Field()
    confirmJobCompleted = confirmJobCompleted.Field()