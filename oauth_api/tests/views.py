from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response


RESPONSE_DATA = {
    'hello': 'world!',
}


class ResourceView(APIView):
    required_scopes = ['read', 'write']

    def get(self, request, *args, **kwargs):
        return Response(RESPONSE_DATA)


class ResourceReadScopesView(APIView):
    read_scopes = ['read']

    def get(self, request, *args, **kwargs):
        return Response(RESPONSE_DATA)


class ResourceWriteScopesView(APIView):
    write_scopes = ['write']

    def post(self, request, *args, **kwargs):
        return Response(RESPONSE_DATA, status=status.HTTP_201_CREATED)


class ResourceReadWriteScopesView(ResourceWriteScopesView, ResourceReadScopesView):
    pass


class ResourceMixedScopesView(ResourceReadWriteScopesView, APIView):
    required_scopes = ['scope1']


class ResourceNoScopesView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(RESPONSE_DATA)
