import json

from django.views.generic import FormView

from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, XMLRenderer
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

    def get(self, request, *args, **kwargs):
        try:
            scopes, credentials = self.validate_authorization_request(self.request)
            self.oauth2_data['scopes'] = scopes
            self.oauth2_data.update(credentials)
            return super(AuthorizationView, self).get(request, *args, **kwargs)
        except (FatalClientError, OAuthAPIError) as error:
            self.oauth2_data['error'] = error
            return self.render_to_response(self.get_context_data(), status=400)

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
            context['error'] = self.oauth2_data['error'].oauthlib_error.error
        return context

    def form_valid(self, form):
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


class TokenView(OAuthViewMixin, APIView):
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (JSONRenderer, XMLRenderer)

    def post(self, request, *args, **kwargs):
        url, headers, body, status = self.create_token_response(request)
        data = json.loads(body)
        return Response(data=data, status=status, headers=headers)
