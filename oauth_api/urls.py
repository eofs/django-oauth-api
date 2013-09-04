from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from oauth_api.views import AuthorizationView, TokenView


urlpatterns = patterns('',
    url(r'^authorize/$', login_required(AuthorizationView.as_view()), name='authorize'),
    url(r'^token/$', TokenView.as_view(), name='token'),
)
