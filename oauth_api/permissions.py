from django.core.exceptions import ImproperlyConfigured

from rest_framework.permissions import BasePermission


class OAuth2ScopePermission(BasePermission):
    """
    Make sure request is authenticated and token has right scope set.
    """
    def has_permission(self, request, view):
        token = request.auth

        if not token:
            return False

        if hasattr(token, 'scope'):
            required_scopes = self.get_scopes(request, view)

            return token.is_valid(required_scopes)

        assert False, ('OAuth2ScopePermission requires the `OAuth2Authentication`'
                       'authentication class to be used.')

    def get_scopes(self, request, view):
        try:
            return getattr(view, 'required_scopes')
        except AttributeError:
            raise ImproperlyConfigured('required_scopes attribute is not defined for this view.')
