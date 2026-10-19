from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from api.graphql_view import BoundedGraphQLView as GraphQLView
from django.conf import settings
from .schema import schema
from api import fayda

graphql_view = csrf_exempt(GraphQLView.as_view(graphiql=settings.DEBUG, schema=schema))
api_view = csrf_exempt(ensure_csrf_cookie(GraphQLView.as_view(graphiql=settings.DEBUG, schema=schema)))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', graphql_view),
    path('api/', api_view),
    path('auth/fayda/start/', fayda.start),
    path('auth/fayda/callback/', fayda.callback),
    path('auth/fayda/complete/', fayda.complete),
]
