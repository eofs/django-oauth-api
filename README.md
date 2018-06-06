Django OAuth API
================

[![Build Status](https://travis-ci.org/eofs/django-oauth-api.png?branch=master)](https://travis-ci.org/eofs/django-oauth-api)

This package provides OAuth API using Django Rest Framework

## Installation
```bash
$ pip install django-oauth-api
```

## Requirements
- Python 2.7 or 3.6
- [Django](https://www.djangoproject.com/) 1.11 or later
- [Django Rest Framework](http://django-rest-framework.org/) 3.8 or later
- [OAuthLib](https://github.com/idan/oauthlib) 2.0.7

## License
Simplified BSD License

## Credits
Big thank you for the people behind [evonove/django-oauth-toolkit](https://github.com/evonove/django-oauth-toolkit)! This project is a fork/heavily based on the work done by them.

## Changes

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
