import graphene
from api.query import Query
from api.mutation import Mutation


schema = graphene.Schema(query=Query, mutation=Mutation)    

