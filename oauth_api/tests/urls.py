from django.conf.urls import include, url

from oauth_api.tests.views import (ResourceView, ResourceReadScopesView,
                                   ResourceWriteScopesView, ResourceReadWriteScopesView,
                                   ResourceMixedScopesView, ResourceNoScopesView)


urlpatterns = [
    url(r'^oauth/', include(('oauth_api.urls', 'oauth_api'), namespace='oauth_api')),
    url(r'^resource-required/', ResourceView.as_view(), name='resource-view'),
    url(r'^resource-read/', ResourceReadScopesView.as_view(), name='resource-read-view'),
    url(r'^resource-write/', ResourceWriteScopesView.as_view(), name='resource-write-view'),
    url(r'^resource-readwrite/', ResourceReadWriteScopesView.as_view(), name='resource-readwrite-view'),
    url(r'^resource-mixed/', ResourceMixedScopesView.as_view(), name='resource-mixed-view'),
    url(r'^resource-noscopes/', ResourceNoScopesView.as_view(), name='resource-noscopes-view'),
]
