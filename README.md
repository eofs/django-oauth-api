Django OAuth API
================

[![CI](https://github.com/eofs/django-oauth-api/actions/workflows/main.yml/badge.svg)](https://github.com/eofs/django-oauth-api/actions/workflows/main.yml)

This package provides OAuth API using Django Rest Framework

## Installation
```bash
$ pip install django-oauth-api
```

## Requirements
- Python 3.8, 3.9 or 3.10
- [Django](https://www.djangoproject.com/) 3.2 or later
- [Django Rest Framework](http://django-rest-framework.org/) 3.13 or later
- [OAuthLib](https://github.com/idan/oauthlib) 2.1.0

## License
Simplified BSD License

## Credits
Big thank you for the people behind [evonove/django-oauth-toolkit](https://github.com/evonove/django-oauth-toolkit)! This project is a fork/heavily based on the work done by them.

## Changes

### 0.8.3 [2022-04-04]

### Added
- GitHub Actions integrated

### Fixed
- Missing migration file added

### 0.8.2 [2022-03-22]

### Update
- `setup.py` now provides long description

### Fixed
- `setup.py` contained incorrect classifier

### 0.8.1 [2022-03-22]

### Updated
- `setup.py` cleanup

### 0.8.0 [2022-03-22]

### Added
- Added support for Python 3.10
- Added support for Django 3.2
- Added support for Django 4.0

### Updated
- Dropped support for Python 3.7
- Dropped support for Django 3.1 and earlier versions

### 0.7.0 [2020-01-30] 

- Update: Added support for Python 3.7 and 3.8
- Update: Added support for Django 2.2 and 3.0
- Update: Dropped compatibility with Python 2.x, Django 1.11 and DRF <3.10
- Update: Removed `djangorestframework-xml` dependency as redundant

### 0.6.3 [2018-08-30]

- Handle request with `None` body value when verifying requests.
- Do not generate client ids with leading or trailing spaces as `AuthorizationView/FormView` strips them away and breaks the flow (and randomly tests too)
- Removed Django 1.10 support
- Added Django 2.1 support
- Fixed Django (master branch) support

### 0.6.2 [2018-08-21]

- Specify `app_name` in `urls.py` to support namespacing in Django 2

### 0.6.1 [2018-06-06]

- Update: Allow overriding of API renderer and parser classes in the settings
- Update: Modified initial migration file that contained South-era bytestrings in verbose names (only Django cares about them, not the DB)

### 0.6.0 [2018-04-13]

- Update: Dropped support for Django <1.11
- Update: Added support for Python 3.6
- Update: Added support for Django 2.0
- Update: Updated to use oauthlib 2.0.7
- Update: Tidying of the codebase here and there

### 0.5.3 [2016-09-22]

- Update: Updated to use oauthlib 1.1.2

### 0.5.2 [2016-04-05]

- Update: Application model is now swappable

### 0.5.1 [2016-02-17]

- Update: Django 1.9 support added

### 0.5.0 [2015-09-04]

- Feature: Token revocation support added
- Update: Updated to use latest oauthlib 1.0.3
- Update: Do not assign user to Access Token if Client Credentials grant used
- Bug: Using public apps with client_id only did not work
