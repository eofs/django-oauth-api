from rest_framework.views import APIView
from rest_framework.response import Response


RESPONSE_DATA = {
    'hello': 'world!',
}

class ResourceView(APIView):
    required_scopes = ['read', 'write']

    def get(self, request, *args, **kwargs):
        return Response(RESPONSE_DATA)
