"""
App configuration for the restaurant application.
This registers the application config with Django.
"""
from django.apps import AppConfig

class RestaurantConfig(AppConfig):
    # Specify the default auto field type for generated database primary keys
    default_auto_field = 'django.db.models.BigAutoField'
    # The Python path to the application
    name = 'restaurant'
