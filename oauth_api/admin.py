from django.contrib import admin

from oauth_api.models import AccessToken, AuthorizationCode, RefreshToken, get_application_model


Application = get_application_model()


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_id', 'created', 'updated')

admin.site.register(Application, ApplicationAdmin)


class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'expires', 'application', 'user', 'created', 'updated')

admin.site.register(AccessToken, AccessTokenAdmin)


class AuthorizationCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'application', 'expires', 'created', 'updated')

admin.site.register(AuthorizationCode, AuthorizationCodeAdmin)


class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'application', 'expires', 'user', 'created', 'updated')
    list_filter = ('expires',)

admin.site.register(RefreshToken, RefreshTokenAdmin)
