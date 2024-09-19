import pytest
from django.conf import settings
from django.apps import apps

@pytest.fixture(scope='session', autouse=True)
def set_django_settings():
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'frontend_app',
            'rest_framework',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'frontend_db',
            }
        },
        ROOT_URLCONF='frontend_app.urls',
        REST_FRAMEWORK = {
            'DEFAULT_RENDERER_CLASSES': [
                'rest_framework.renderers.JSONRenderer',
                'rest_framework.renderers.BrowsableAPIRenderer', 
        ]}
# }
    )
    apps.populate(settings.INSTALLED_APPS)