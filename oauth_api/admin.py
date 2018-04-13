from django.contrib import admin

from oauth_api.models import AccessToken, AuthorizationCode, RefreshToken, get_application_model


Application = get_application_model()


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_id', 'created', 'updated')


class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'expires', 'application', 'user', 'created', 'updated')


class AuthorizationCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'application', 'expires', 'created', 'updated')


class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'application', 'expires', 'user', 'created', 'updated')
    list_filter = ('expires',)


admin.site.register(Application, ApplicationAdmin)
admin.site.register(AccessToken, AccessTokenAdmin)
admin.site.register(AuthorizationCode, AuthorizationCodeAdmin)
admin.site.register(RefreshToken, RefreshTokenAdmin)
