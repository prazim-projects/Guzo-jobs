import graphene

class UserType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    email = graphene.String()
    phone_number = graphene.String()
    profile_picture = graphene.String()
    bio = graphene.String()

class ContractType(graphene.ObjectType):
    id = graphene.ID()
    job_post = graphene.Field(lambda: JobPostingType)
    poster = graphene.Field(UserType)
    acceptor = graphene.Field(UserType)
    status = graphene.String()
    agreed_price = graphene.Float()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()

    def resolve_job_post(self, info):
        return self.job_post

    def resolve_poster(self, info):
        return self.poster

    def resolve_acceptor(self, info):
        return self.acceptor

class JobPostingType(graphene.ObjectType):
    id = graphene.ID()
    title = graphene.String()
    description = graphene.String()
    user = graphene.Field(UserType)
    expires_at = graphene.DateTime()
    origin = graphene.String()
    destination = graphene.String()
    post_type = graphene.String()
    contracts = graphene.List(ContractType)
    price = graphene.Float()

    def resolve_user(self, info):
        return self.user

    def resolve_contracts(self, info):
        return self.contract.all()
