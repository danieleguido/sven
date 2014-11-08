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
import os, sys
import local_settings
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SVEN_NAME = local_settings.SVEN_NAME

# load local pattern
MODULE = os.path.join(BASE_DIR, 'pattern')
if MODULE not in sys.path:
  sys.path.append(MODULE)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = local_settings.SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = local_settings.DEBUG
ALLOWED_HOSTS = local_settings.ALLOWED_HOSTS
TEMPLATE_DEBUG = True
CORS_ORIGIN_ALLOW_ALL = True
# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sven',
    'glue',
    'twit'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)

ROOT_URLCONF = 'sven.urls'

WSGI_APPLICATION = 'sven.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': local_settings.DB_ENGINE,
        'NAME': local_settings.DB_NAME,
        'USER': local_settings.DB_USER,
        'PASSWORD': local_settings.DB_PASS,
        'HOST': local_settings.DB_HOST,
        'PORT': local_settings.DB_PORT
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
STATIC_ROOT = local_settings.STATIC_ROOT
STATIC_URL = local_settings.STATIC_URL
STATIC_ROOT = local_settings.STATIC_ROOT
MEDIA_ROOT = local_settings.MEDIA_ROOT
MEDIA_URL = local_settings.MEDIA_URL

LOGIN_URL = '/login/'

STATICFILES_DIRS = (
  os.path.join(BASE_DIR, 'client'),
)

TEMPLATE_DIRS = (
  os.path.join(BASE_DIR, 'client'),
)

PYTHON_INTERPRETER = local_settings.PYTHON_INTERPRETER

ENABLE_CDN_SERVICES = local_settings.ENABLE_CDN_SERVICES

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
            'format': u'%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d «%(message)s»'
      },
      'simple': {
            'format': u'%(asctime)s «%(message)s» %(module)s.%(funcName)s (%(lineno)s)'
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

# sven management stuffs
FREEBASE_KEY = local_settings.FREEBASE_KEY
ALCHEMYAPI_KEY = local_settings.ALCHEMYAPI_KEY
TWITTER_CONSUMER_KEY = local_settings.TWITTER_CONSUMER_KEY
TWITTER_CONSUMER_SECRET = local_settings.TWITTER_CONSUMER_SECRET
TWITTER_ACCESS_TOKEN = local_settings.TWITTER_ACCESS_TOKEN
TWITTER_ACCESS_TOKEN_SECRET = local_settings.TWITTER_ACCESS_TOKEN_SECRET


WHOOSH_PATH     = os.path.join(BASE_DIR, 'contents/whoosh')
STOPWORDS_PATH  = os.path.join(BASE_DIR, 'contents/stopwords') # Cfr models.Corpus.get_stopwords_path(). Path where txt stopwords files has to be stored.
CSV_PATH        = os.path.join(BASE_DIR, 'contents/csv') # Cfr models.Corpus.get_csv_path(). Path where csv files has to be stored.

STANDALONE_COMMANDS = ['harvest', 'whoosher', 'freebase'] # standalone management commands.
