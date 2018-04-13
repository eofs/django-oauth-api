try:
    # Python 2
    from urlparse import urlparse, parse_qs
except ImportError:
    # Python 3
    from urllib.parse import urlparse, parse_qs


try:
    # Django 1.11
    from django.core.urlresolvers import reverse
except ImportError:
    # Django 2.0
    from django.urls import reverse
