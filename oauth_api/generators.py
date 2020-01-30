from oauthlib.common import CLIENT_ID_CHARACTER_SET, generate_client_id as oauthlib_generate_client_id


from oauth_api.settings import oauth_api_settings


class BaseGenerator(object):
    """
    Base generator, subclass this before use.

    The defined `charset` attribute should be used to generate client id and secret values. It is a
    copy of the `oauthlib` charset, but with the space character removed.
    """
    charset = CLIENT_ID_CHARACTER_SET.replace(' ', '')

    def hash(self):
        raise NotImplementedError('.hash() must be overridden.')


class ClientIdGenerator(BaseGenerator):
    def hash(self):
        """
        Generate client id without colon char as in http://tools.ietf.org/html/rfc2617#section-2
        for Basic Authentication scheme.
        """
        return oauthlib_generate_client_id(length=64, chars=self.charset.replace(':', ''))


class ClientSecretGenerator(BaseGenerator):
    def hash(self):
        """
        Generate client secret
        """
        return oauthlib_generate_client_id(length=128, chars=self.charset)


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
