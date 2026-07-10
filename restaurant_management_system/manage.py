#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

This script acts as the entry point for running administrative commands in Django:
- Running migrations (python manage.py migrate)
- Starting the development server (python manage.py runserver)
- Creating superusers (python manage.py createsuperuser)
- Running unit tests (python manage.py test)
- Creating new applications (python manage.py startapp)
"""
import os
import sys

def main():
    """Run administrative tasks."""
    # Set the default settings module for the 'restaurant_management_system' project.
    # This instructs Django which settings file to use.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management_system.settings')
    
    try:
        # Import Django's management execution function
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
        
    # Execute commands passed in via command line (e.g. sys.argv)
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
