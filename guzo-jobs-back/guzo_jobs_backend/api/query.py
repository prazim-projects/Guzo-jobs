import graphene
from graphene_django import DjangoObjectType

from .models import UserProfile, JobPosting
from .types import UserType, JobPostingType

class Query(graphene.ObjectType):
    allUsers = graphene.List(UserType)
    user_by_id = graphene.Field(UserType, id=graphene.ID(required=True))
    allJobs = graphene.Field(graphene.List(lambda: JobPostingType))


    def resolve_allUsers(root, info):
        return UserProfile.objects.all()
    
    def resolve_user_by_id(root, info, id):
        try:
            return UserProfile.objects.get(pk=id)
        except UserProfile.DoesNotExist:
            return None
        
    def resolve_allJobs(root, info):
        return JobPosting.objects.select_related('user').all()