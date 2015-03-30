import importlib

from django.conf import settings
from django.utils import six


USER_SETTINGS = getattr(settings, 'OAUTH_API', None)


DEFAULTS = {
    'ACCESS_TOKEN_EXPIRATION': 3600, # Seconds
    'REFRESH_TOKEN_EXPIRATION': None, # Seconds, (None == disabled)
    'APPLICATION_MODEL': 'oauth_api.Application',
    'CLIENT_ID_GENERATOR': 'oauth_api.generators.ClientIdGenerator',
    'CLIENT_SECRET_GENERATOR': 'oauth_api.generators.ClientSecretGenerator',
    'DEFAULT_HANDLER_CLASS': 'oauth_api.handlers.OAuthHandler',
    'DEFAULT_SERVER_CLASS': 'oauthlib.oauth2.Server',
    'DEFAULT_VALIDATOR_CLASS': 'oauth_api.validators.OAuthValidator',
    'SCOPES': {
        'read': 'Read access',
        'write': 'Write access',
    },
}


IMPORT_STRINGS = (
    'CLIENT_ID_GENERATOR',
    'CLIENT_SECRET_GENERATOR',
    'DEFAULT_HANDLER_CLASS',
    'DEFAULT_SERVER_CLASS',
    'DEFAULT_VALIDATOR_CLASS',
)


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.

    Credits to Django Rest Framework project.
    http://django-rest-framework.org/
    """
    if val is None:
        return None
    elif isinstance(val, six.string_types):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        # Nod to tastypie's use of importlib.
        parts = val.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except ImportError as e:
        msg = "Could not import '%s' for API setting '%s'. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


class OAuthApiSettings(object):
    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        self.user_settings = user_settings or {}
        self.defaults = defaults or {}
        self.import_strings = import_strings or ()

    def __getattr__(self, attr):
        if attr not in self.defaults.keys():
            raise AttributeError('Invalid setting: %s' % attr)

        try:
            val = self.user_settings[attr]
        except KeyError:
            val = self.defaults[attr]

        if val and attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache
        setattr(self, attr, val)
        return val


oauth_api_settings = OAuthApiSettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)
