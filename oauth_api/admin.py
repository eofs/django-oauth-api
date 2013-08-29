from django.contrib import admin

from oauth_api.models import AccessToken, RefreshToken, get_application_model


Application = get_application_model()


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_id', 'created', 'updated')

admin.site.register(Application, ApplicationAdmin)


class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'expires', 'application', 'user')

admin.site.register(AccessToken, AccessTokenAdmin)


admin.site.register(RefreshToken)
