"""
ASGI config for restaurant_management_system project.

It exposes the ASGI callable as a module-level variable named `application`.

Asynchronous Server Gateway Interface (ASGI) is the specification for asynchronous
Python web applications to communicate with web servers (such as Uvicorn or Daphne).
This is useful for real-time services like WebSockets or asynchronous HTTP handlers.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Point Django settings environment variable to our settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management_system.settings')

# Get the ASGI application callable
application = get_asgi_application()
