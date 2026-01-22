from .models import UserProfile, JobPosting
import graphene

class UserType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    email = graphene.String()
    bio = graphene.String()

class JobPostingType(graphene.ObjectType):
    id = graphene.ID()
    title = graphene.String()
    description = graphene.String()
    user = graphene.Field(UserType)
    expires_at = graphene.DateTime()
    origin = graphene.String()
    destination = graphene.String()
    post_type = graphene.String()