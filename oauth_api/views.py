import json


from rest_framework.views import APIView
from rest_framework.response import Response

from oauth_api.mixins import OAuthViewMixin


class TokenView(OAuthViewMixin, APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        url, headers, body, status = self.create_token_response(request)
        data = json.loads(body)
        return Response(data=data, status=status, headers=headers)
