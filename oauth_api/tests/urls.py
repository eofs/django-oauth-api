from django.urls import include, path

from oauth_api.tests.views import (ResourceView, ResourceReadScopesView,
                                   ResourceWriteScopesView, ResourceReadWriteScopesView,
                                   ResourceMixedScopesView, ResourceNoScopesView)


urlpatterns = [
    path('oauth/', include(('oauth_api.urls', 'oauth_api'), namespace='oauth_api')),
    path('resource-required/', ResourceView.as_view(), name='resource-view'),
    path('resource-read/', ResourceReadScopesView.as_view(), name='resource-read-view'),
    path('resource-write/', ResourceWriteScopesView.as_view(), name='resource-write-view'),
    path('resource-readwrite/', ResourceReadWriteScopesView.as_view(), name='resource-readwrite-view'),
    path('resource-mixed/', ResourceMixedScopesView.as_view(), name='resource-mixed-view'),
    path('resource-noscopes/', ResourceNoScopesView.as_view(), name='resource-noscopes-view'),
]
