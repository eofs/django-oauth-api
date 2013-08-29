from django.conf.urls import patterns, url

from oauth_api.views import TokenView


urlpatterns = patterns('',
    url(r'^token/$', TokenView.as_view(), name='token'),
)
