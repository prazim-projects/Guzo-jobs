import graphene
from api.query import Query

schema = graphene.Schema(query=Query)    

