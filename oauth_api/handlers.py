class OAuthHandler(object):
    def __init__(self, server):
        self.server = server

    def extract_params(self, request):
        data = request.DATA
        headers = request._request.META.copy()
        method = request.method
        uri = request._request.build_absolute_uri()
        if 'wsgi.input' in headers:
            del headers['wsgi.input']
        if 'wsgi.errors' in headers:
            del headers['wsgi.errors']
        return uri, method, data, headers

    def create_token_response(self, request):
        uri, method, data, headers = self.extract_params(request)
        url, headers, body, status = self.server.create_token_response(uri, method, data, headers)
        return url, headers, body, status

