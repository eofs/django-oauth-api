from django.apps import apps
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


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

    GRANT_AUTHORIZATION_CODE = 'authorization-code'
    GRANT_IMPLICIT = 'implicit'
    GRANT_PASSWORD = 'password'
    GRANT_CLIENT_CREDENTIALS = 'client-credentials'
    GRANT_TYPES = (
        (GRANT_AUTHORIZATION_CODE, _('Authorization code')),
        (GRANT_IMPLICIT, _('Implicit')),
        (GRANT_PASSWORD, _('Resource owner password-based')),
        (GRANT_CLIENT_CREDENTIALS, _('Client credentials')),
    )

    created = models.DateTimeField('created', auto_now_add=True)
    updated = models.DateTimeField('updated', auto_now=True)

    client_id = models.CharField(max_length=100, unique=True,
                                 default=generate_client_id)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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

    def clean(self):
        redirect_uris_required_for = (AbstractApplication.GRANT_AUTHORIZATION_CODE, AbstractApplication.GRANT_IMPLICIT)
        if not self.redirect_uris and self.authorization_grant_type in redirect_uris_required_for:
            error = _('Redirect URIs required when {0} grant_type used')
            raise ValidationError(error.format(self.authorization_grant_type))

    @property
    def default_redirect_uri(self):
        """
        Returns the default redirect uri by extracting first in the list of uris.
        """
        if self.redirect_uris:
            return self.redirect_uris.split().pop(0)
        return None

    def redirect_uri_allowed(self, redirect_uri):
        """
        Check if redirect uri is valid for current application.
        """
        return redirect_uri in self.redirect_uris.split()

    def __str__(self):
        return self.name


class Application(AbstractApplication):
    pass


class AccessToken(models.Model):
    """
    This model represents the actual access token to access user's resources.
    """
    created = models.DateTimeField('created', auto_now_add=True)
    updated = models.DateTimeField('updated', auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    token = models.CharField(max_length=255, db_index=True)
    application = models.ForeignKey(oauth_api_settings.APPLICATION_MODEL, on_delete=models.CASCADE, swappable=True)
    expires = models.DateTimeField()
    scope = models.TextField(blank=True)

    def allow_scopes(self, scopes):
        """
        Check if token allows the provided scopes.
        """
        if not scopes:
            return True

        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)

    @property
    def is_expired(self):
        """
        Check if token has been expired.
        """
        return timezone.now() >= self.expires

    def is_valid(self, scopes=None):
        """
        Check if access token is valid.
        """
        return not self.is_expired and self.allow_scopes(scopes)

    def revoke(self):
        # Alias to make it easier for revocation endpoint to delete tokens
        self.delete()


class AuthorizationCode(models.Model):
    created = models.DateTimeField('created', auto_now_add=True)
    updated = models.DateTimeField('updated', auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=255)
    application = models.ForeignKey(oauth_api_settings.APPLICATION_MODEL, on_delete=models.CASCADE, swappable=True)
    expires = models.DateTimeField()
    redirect_uri = models.CharField(max_length=255)
    scope = models.TextField(blank=True)

    @property
    def is_expired(self):
        """
        Check if code has been expired.
        """
        return timezone.now() >= self.expires

    def redirect_uri_allowed(self, redirect_uri):
        return redirect_uri == self.redirect_uri


class RefreshToken(models.Model):
    """
    This model represents the actual refresh token.
    """
    created = models.DateTimeField('created', auto_now_add=True)
    updated = models.DateTimeField('updated', auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    expires = models.DateTimeField(null=True, blank=True)
    application = models.ForeignKey(oauth_api_settings.APPLICATION_MODEL, on_delete=models.CASCADE, swappable=True)
    access_token = models.OneToOneField(AccessToken, on_delete=models.CASCADE, related_name='refresh_token')

    @property
    def is_expired(self):
        """
        Check if code has been expired.
        """
        if self.expires is None:
            return False
        return timezone.now() >= self.expires

    def revoke(self):
        """
        Revoke (delete) refresh token and related access token
        """
        self.access_token.delete()
        self.delete()


def get_application_model():
    """
    Return active Appliation model. Use settings to override active model.
    """
    try:
        app_label, model_name = oauth_api_settings.APPLICATION_MODEL.split('.')
    except ValueError:
        raise ImproperlyConfigured("APPLICATION_MODEL must be in the form of 'app_label.model_name'")
    app_model = apps.get_model(app_label, model_name)
    if app_model is None:
        raise ImproperlyConfigured("APPLICATION_MODEL refers to model that is not available.")
    return app_model
