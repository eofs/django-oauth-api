from django.core.validators import URLValidator


def validate_uris(value):
    """
    Validate list of newline separated urls
    """
    v = URLValidator()
    for uri in value.split():
        v(uri)
