from rest_framework.permissions import BasePermission


SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


class OAuth2ScopePermission(BasePermission):
    """
    Make sure request is authenticated and token has right scope set.
    """
    def has_permission(self, request, view):
        token = request.auth
        read_only = request.method in SAFE_METHODS

        if not token:
            return False

        if hasattr(token, 'scope'):
            scopes = self.get_scopes(request, view)
            if scopes['required'] is not None:
                is_valid = token.is_valid(scopes['required'])
                if is_valid == False:
                    return False
            else:
                # View did not define any required scopes
                is_valid = False

            # Check for method specific scopes
            if read_only:
                if scopes['read'] is not None:
                    return token.is_valid(scopes['read'])
            else:
                if scopes['write'] is not None:
                    return token.is_valid(scopes['write'])

            return is_valid

        return False

    def get_scopes(self, request, view):
        return {
            'required': getattr(view, 'required_scopes', None),
            'read': getattr(view, 'read_scopes', None),
            'write': getattr(view, 'write_scopes', None),
        }
