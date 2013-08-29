from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import get_model
from django.conf import settings
from django.utils.translation import ugettext as _


from oauth_api.generators import generate_client_id, generate_client_secret
from oauth_api.settings import oauth_api_settings
from oauth_api.utils import validate_uris


class AbstractApplication(models.Model):
    """
    This model represents Client on the Authorization server.
    """
    CLIENT_CONFIDENTIAL = 'confidential'
    CLIENT_PUBLIC = 'public'
    CLIENT_TYPES = (
        (CLIENT_CONFIDENTIAL, _('Confidential')),
        (CLIENT_PUBLIC, _('Public')),
    )

    GRANT_ALLINONE = 'all-in-one'
    GRANT_AUTHORIZATION_CODE = 'authorization-code'
    GRANT_IMPLICIT = 'implicit'
    GRANT_PASSWORD = 'password'
    GRANT_CLIENT_CREDENTIALS = 'client-credentials'
    GRANT_TYPES = (
        (GRANT_ALLINONE, _('All-in-one generic')),
        (GRANT_AUTHORIZATION_CODE, _('Authorization code')),
        (GRANT_IMPLICIT, _('Implicit')),
        (GRANT_PASSWORD, _('Resource owner password-based')),
        (GRANT_CLIENT_CREDENTIALS, _('Client credentials')),
    )


    created = models.DateTimeField('created', auto_now_add=True)
    updated = models.DateTimeField('updated', auto_now=True)

    client_id = models.CharField(max_length=100, unique=True,
                                 default=generate_client_id)

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    help_text = _('Allowed URIs list, line separated')
    redirect_uris = models.TextField(help_text=help_text,
                                     validators=[validate_uris], blank=True)
    client_type = models.CharField(max_length=32, choices=CLIENT_TYPES)
    authorization_grant_type = models.CharField(max_length=32,
                                                choices=GRANT_TYPES)
    client_secret = models.CharField(max_length=255, blank=True,
                                     default=generate_client_secret)
    name = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name


class Application(AbstractApplication):
    pass


class AccessToken(models.Model):
    """
    This model represents the actual access token to access user's resources.
    """
    created = models.DateTimeField('created', auto_now_add=True)
    updated = models.DateTimeField('updated', auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    token = models.CharField(max_length=255)
    application = models.ForeignKey(oauth_api_settings.APPLICATION_MODEL)
    expires = models.DateTimeField()
    scope = models.TextField(blank=True)


class RefreshToken(models.Model):
    """
    This model represents the actual refresh token.
    """
    created = models.DateTimeField('created', auto_now_add=True)
    updated = models.DateTimeField('updated', auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    token = models.CharField(max_length=255)
    application = models.ForeignKey(oauth_api_settings.APPLICATION_MODEL)
    access_token = models.OneToOneField(AccessToken,
                                        related_name='refresh_token')

def get_application_model():
    """
    Return active Appliation model. Use settings to override active model.
    """
    try:
        app_label, model_name = oauth_api_settings.APPLICATION_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured("APPLICATION_MODEL must be in the form of 'app_label.model_name'")
    app_model = get_model(app_label, model_name)
    if app_model is None:
        raise ImproperlyConfigured("APPLICATION_MODEL refers to model that is not available.")
    return app_model
