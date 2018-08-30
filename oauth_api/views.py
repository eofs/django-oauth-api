import json

from django.http import HttpResponseRedirect
from django.views.generic import FormView

from rest_framework import status as http_status
from rest_framework.views import APIView
from rest_framework.response import Response

from oauth_api.forms import AuthorizationForm
from oauth_api.mixins import OAuthViewMixin
from oauth_api.models import get_application_model
from oauth_api.exceptions import FatalClientError, OAuthAPIError
from oauth_api.settings import oauth_api_settings

Application = get_application_model()


class AuthorizationView(OAuthViewMixin, FormView):
    template_name = 'oauth_api/authorize.html'
    form_class = AuthorizationForm

    def dispatch(self, request, *args, **kwargs):
        self.oauth2_data = {}
        return super(AuthorizationView, self).dispatch(request, *args, **kwargs)

    def error_response(self, error, **kwargs):
        """
        Redirect user-agent back to origin. Origin is determined from detected client.
        """
        oauthlib_error = error.oauthlib_error
        url = '{0}?{1}'.format(oauthlib_error.redirect_uri, oauthlib_error.urlencoded)
        return HttpResponseRedirect(url)

    def get(self, request, *args, **kwargs):
        try:
            scopes, credentials = self.validate_authorization_request(self.request)
            self.oauth2_data['scopes'] = scopes
            self.oauth2_data.update(credentials)
            return super(AuthorizationView, self).get(request, *args, **kwargs)
        except FatalClientError as error:
            # Fatal error, could not determine client
            self.oauth2_data['error'] = error
            return self.render_to_response(self.get_context_data(), status=http_status.HTTP_400_BAD_REQUEST)
        except OAuthAPIError as error:
            # Redirect user-agent back to origin
            return self.error_response(error)

    def get_initial(self):
        return {
            'client_id': self.oauth2_data.get('client_id', None),
            'redirect_uri': self.oauth2_data.get('redirect_uri', None),
            'response_type': self.oauth2_data.get('response_type', None),
            'scopes': ' '.join(self.oauth2_data.get('scopes', [])),
            'state': self.oauth2_data.get('state', None),
        }

    def get_context_data(self, **kwargs):
        context = super(AuthorizationView, self).get_context_data(**kwargs)
        if 'error' not in self.oauth2_data:
            scopes = self.oauth2_data['scopes']
            context['application'] = Application.objects.get(client_id=self.oauth2_data['client_id'])
            context['scopes_descriptions'] = [oauth_api_settings.SCOPES[scope] for scope in scopes]
            context.update(self.oauth2_data)
        else:
            context['error'] = self.oauth2_data['error'].oauthlib_error
        return context

    def form_valid(self, form):
        try:
            credentials = {
                'client_id': form.cleaned_data.get('client_id', None),
                'redirect_uri': form.cleaned_data.get('redirect_uri', None),
                'response_type': form.cleaned_data.get('response_type', None),
                'state': form.cleaned_data.get('state', None),
            }

            scopes = form.cleaned_data.get('scopes', None)
            allow = form.cleaned_data.get('allow', False)

            uri, headers, body, status = self.create_authorization_response(
                request=self.request, scopes=scopes, credentials=credentials, allow=allow)
            self.success_url = uri
            return super(AuthorizationView, self).form_valid(form)
        except FatalClientError as error:
            # Do not redirect resource owner
            self.oauth2_data['error'] = error
            return self.render_to_response(self.get_context_data(form=form), status=http_status.HTTP_400_BAD_REQUEST)
        except OAuthAPIError as error:
            # Redirect resource owner
            return self.error_response(error)


class TokenBaseView(OAuthViewMixin, APIView):
    authentication_classes = ()
    permission_classes = ()


class TokenView(TokenBaseView):
    def post(self, request, *args, **kwargs):
        url, headers, body, status = self.create_token_response(request)
        data = json.loads(body)
        return Response(data=data, status=status, headers=headers)


class TokenRevocationView(TokenBaseView):
    def post(self, request, *args, **kwargs):
        url, headers, body, status = self.create_revocation_response(request)
        return Response(status=status, headers=headers)
