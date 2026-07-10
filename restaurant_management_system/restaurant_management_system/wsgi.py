"""
WSGI config for restaurant_management_system project.

It exposes the WSGI callable as a module-level variable named `application`.

Web Server Gateway Interface (WSGI) is the standard specification for Python
web applications to communicate with web servers (such as Gunicorn, uWSGI, or Apache mod_wsgi).
This is the standard deployment gateway for synchronous Django setups.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Point Django settings environment variable to our settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management_system.settings')

# Get the WSGI application callable
application = get_wsgi_application()
