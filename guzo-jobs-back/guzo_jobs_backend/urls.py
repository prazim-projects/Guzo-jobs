from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from graphene_django.views import GraphQLView
from .schema import schema

graphql_view = csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))
api_view = csrf_exempt(ensure_csrf_cookie(GraphQLView.as_view(graphiql=True, schema=schema)))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', graphql_view),
    path('api/', api_view),
]
