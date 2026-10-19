"""Isolated audit settings. Only used by scripts/audit_backend.py, never deployment."""
from .settings import *  # noqa: F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
SECURE_SSL_REDIRECT = False  # HTTP test client; deploy audit reads production defaults separately.
# Preserve the real password hasher and JWT/security defaults under audit.
