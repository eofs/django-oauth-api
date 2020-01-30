from django.urls import path
from django.contrib.auth.decorators import login_required

from oauth_api.views import AuthorizationView, TokenView, TokenRevocationView

app_name = 'oauth_api'

urlpatterns = [
    path('authorize/', login_required(AuthorizationView.as_view()), name='authorize'),
    path('token/', TokenView.as_view(), name='token'),
    path('revoke_token/', TokenRevocationView.as_view(), name='revoke-token'),
]
