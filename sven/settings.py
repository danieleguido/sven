#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Django settings for ss project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import local_settings
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SVEN_NAME = local_settings.SVEN_NAME

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = local_settings.SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sven',
    'glue'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'sven.urls'

WSGI_APPLICATION = 'sven.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': local_settings.DB_ENGINE,
        'NAME': local_settings.DB_NAME,
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = local_settings.LANGUAGE_CODE

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = local_settings.STATIC_URL

MEDIA_ROOT = local_settings.MEDIA_ROOT

LOGIN_URL = '/login/'

STATICFILES_DIRS = (
  os.path.join(BASE_DIR, 'static'),
)

TEMPLATE_DIRS = (
  os.path.join(BASE_DIR, 'templates'),
)

PYTHON_INTERPRETER = local_settings.PYTHON_INTERPRETER


EN = 'en'
IT = 'it'
FR = 'fr'
NL = 'nl'

LANGUAGE_CHOICES = (
  (EN, u'english'),
  (FR, u'french'),
  (NL, u'dutch'),
  (IT, u'italian'),
)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
      'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d «%(message)s»'
      },
      'simple': {
            'format': '%(asctime)s «%(message)s» %(module)s.%(funcName)s (%(lineno)s)'
      },
    },
    'handlers': {
      'file': {
          'level': 'DEBUG',
          'class': 'logging.FileHandler',
          'filename': os.path.join(BASE_DIR, 'logs/debug.log'),
          'formatter': 'simple'
      },
    },
    'loggers': {
        'sven': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


LOG_FILE = LOGGING['handlers']['file']['filename']