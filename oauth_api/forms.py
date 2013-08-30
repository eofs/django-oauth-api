from django import forms


class AuthorizationForm(forms.Form):
    allow = forms.BooleanField(required=False)
    client_id = forms.CharField(widget=forms.HiddenInput())
    redirect_uri = forms.CharField(widget=forms.HiddenInput())
    response_type = forms.CharField(widget=forms.HiddenInput())
    scopes = forms.CharField(required=False, widget=forms.HiddenInput())
    state = forms.CharField(required=False, widget=forms.HiddenInput())
