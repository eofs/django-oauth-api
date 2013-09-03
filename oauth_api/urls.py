from django.conf.urls import patterns, url

from oauth_api.views import AuthorizationView, TokenView


urlpatterns = patterns('',
    url(r'^authorize/$', AuthorizationView.as_view(), name='authorize'),
    url(r'^token/$', TokenView.as_view(), name='token'),
)
