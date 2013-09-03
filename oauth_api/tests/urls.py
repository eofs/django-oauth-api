from django.conf.urls import patterns, include, url

from oauth_api.tests.views import ResourceView


urlpatterns = patterns('',
    url(r'^oauth/', include('oauth_api.urls', namespace='oauth_api')),
    url(r'^resource/', ResourceView.as_view(), name='resource-view'),
)
