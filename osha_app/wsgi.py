"""
WSGI config for osha_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

import platform

# macOS/Homebrew fix for WeasyPrint/Pango/Cairo
if platform.system() == 'Darwin':
    os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "osha_app.settings")

application = get_wsgi_application()
