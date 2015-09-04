from oauth_api.exceptions import FatalClientError
from oauth_api.settings import oauth_api_settings


class OAuthViewMixin(object):
    """
    Base mixin for all views.
    """

    oauth_handler_class = None
    oauth_server_class = None
    oauth_validator_class = None

    def error_response(self, error, **kwargs):
        """
        Return an error to be displayed.
        """
        oauthlib_error = error.oauthlib_error
        error_response = {
            'error': oauthlib_error,
            'url': '{0}?{1}'.format(oauthlib_error.redirect_uri, oauthlib_error.urlencoded)
        }
        error_response.update(kwargs)

        if isinstance(error, FatalClientError):
            redirect = False
        else:
            redirect = True

        return redirect, error_response

    def get_server(self):
        """
        Return an instance of `oauth_server_class` initialized with a `oauth_validator_class`
        """
        server_class = self.get_server_class()
        validator_class = self.get_validator_class()
        return server_class(validator_class(), token_expires_in=oauth_api_settings.ACCESS_TOKEN_EXPIRATION)

    def get_server_class(self):
        """
        Return the class to use for the endpoint.
        Defaults to `oauthlib.oauth2.Server`.
        """
        server_class = self.oauth_server_class
        if server_class is not None:
            return server_class
        return oauth_api_settings.DEFAULT_SERVER_CLASS

    def get_validator_class(self):
        """
        Return the class to use validating the request.
        Defaults to `oauth_api.validators.OAuthValidator`.
        """
        validator_class = self.oauth_validator_class
        if validator_class is not None:
            return validator_class
        return oauth_api_settings.DEFAULT_VALIDATOR_CLASS

    def get_handler_class(self):
        """
        Return the class to use with request data.
        Defaults to `oauth_api.handlers.RequestHandler.`
        """
        handler_class = self.oauth_handler_class
        if handler_class is not None:
            return handler_class
        return oauth_api_settings.DEFAULT_HANDLER_CLASS

    def get_request_handler(self):
        """
        Return request handler instance from cache. New instance will be created if not available otherwise.
        """
        if not hasattr(self, '_oauth_handler'):
            handler_class = self.get_handler_class()
            server = self.get_server()
            self._oauth_handler = handler_class(server)
        return self._oauth_handler

    def create_authorization_response(self, request, scopes, credentials, allow):
        scopes = scopes.split(' ') if scopes else []
        handler = self.get_request_handler()
        return handler.create_authorization_response(request, scopes, credentials, allow)

    def create_token_response(self, request):
        handler = self.get_request_handler()
        return handler.create_token_response(request)

    def create_revocation_response(self, request):
        handler = self.get_request_handler()
        return handler.create_revocation_response(request)

    def validate_authorization_request(self, request):
        handler = self.get_request_handler()
        return handler.validate_authorization_request(request)
