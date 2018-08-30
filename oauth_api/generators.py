from oauthlib.common import CLIENT_ID_CHARACTER_SET, generate_client_id as oauthlib_generate_client_id


from oauth_api.settings import oauth_api_settings


class BaseGenerator(object):
    """
    Base generator, subclass this before use.
    """
    def hash(self):
        raise NotImplementedError('.hash() must be overridden.')


class ClientIdGenerator(BaseGenerator):
    def hash(self):
        """
        Generate client id without colon char as in http://tools.ietf.org/html/rfc2617#section-2
        for Basic Authentication scheme.
        """
        client_id_charset = CLIENT_ID_CHARACTER_SET.replace(':', '')
        client_id = oauthlib_generate_client_id(length=64, chars=client_id_charset)
        # Ignore IDs with leading/trailing spaces as AuthorizationView/FormView strips them away...
        while len(client_id.strip()) < 64:
            client_id = oauthlib_generate_client_id(length=64, chars=client_id_charset)
        return client_id


class ClientSecretGenerator(BaseGenerator):
    def hash(self):
        """
        Generate client secret
        """
        return oauthlib_generate_client_id(length=128)


def generate_client_id():
    """
    Generate client id
    """
    client_id_generator = oauth_api_settings.CLIENT_ID_GENERATOR()
    return client_id_generator.hash()


def generate_client_secret():
    """
    Generate client secret
    """
    client_secret_generator = oauth_api_settings.CLIENT_SECRET_GENERATOR()
    return client_secret_generator.hash()
