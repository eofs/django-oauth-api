from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^oauth/', include('oauth_api.urls', namespace='oauth_api')),
)
