import pytest
from django.apps import apps
from django.conf import settings


@pytest.fixture(scope="session", autouse=True)
def set_django_settings():
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "admin_app",
            "rest_framework",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.mysql",
                "NAME": "admin_db",
            }
        },
        ROOT_URLCONF="admin_app.urls",
        REST_FRAMEWORK={
            "DEFAULT_RENDERER_CLASSES": [
                "rest_framework.renderers.JSONRenderer",
                "rest_framework.renderers.BrowsableAPIRenderer",
            ]
        }
        # }
    )
    apps.populate(settings.INSTALLED_APPS)
