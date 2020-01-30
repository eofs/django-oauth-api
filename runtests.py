#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oauth_api.tests.settings")

    args = [sys.argv[0], 'test']
    args.extend(sys.argv[1:])

    from django.core.management import execute_from_command_line
    execute_from_command_line(args)
