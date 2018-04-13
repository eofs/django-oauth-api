class OAuthAPIError(Exception):
    """
    Base exception

    If raised, user-agent should be redirected back to origin (default redirect_uri in client)
    """
    def __init__(self, error=None, redirect_uri=None, *args, **kwargs):
        super(OAuthAPIError, self).__init__(*args, **kwargs)
        self.oauthlib_error = error

        if redirect_uri:
            self.oauthlib_error.redirect_uri = redirect_uri


class FatalClientError(OAuthAPIError):
    """
    Critical error

    If raised, display error to usage-agent, do not redirect.
    """
    pass
