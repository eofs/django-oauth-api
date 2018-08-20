from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from oauth_api.views import AuthorizationView, TokenView, TokenRevocationView

app_name = 'oauth_api'
urlpatterns = [
    url(r'^authorize/$', login_required(AuthorizationView.as_view()), name='authorize'),
    url(r'^token/$', TokenView.as_view(), name='token'),
    url(r'^revoke_token/$', TokenRevocationView.as_view(), name='revoke-token'),
]
