from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from graphene_django.views import GraphQLView
from .schema import schema

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', GraphQLView.as_view(graphiql=True, schema=schema)),
    path('api/',ensure_csrf_cookie(GraphQLView.as_view(graphiql=True, schema=schema))),
]
