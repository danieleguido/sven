import os

DEBUG = True
ALLOWED_HOSTS = []

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SVEN_NAME = 'SVEN'
DEBUG = False
ALLOWED_HOSTS = [] # change this according to the documentation

SECRET_KEY = 'your own generated secret key'

DB_ENGINE = 'django.db.backends.sqlite3'
DB_NAME = os.path.join(BASE_DIR, 'sqlite/db.sqlite3') # given as example

LANGUAGE_CODE = 'en-us'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'dist')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

LANGUAGE_CODE = 'en-US'

PYTHON_INTERPRETER = '/home/daniele/.virtualenvs/sven/bin/python' # mine, given as exemple. Cfr virtualenv doc.

ENABLE_CDN_SERVICES = False # set to true if you want to use CDN. This const will be used in templates

FREEBASE_KEY = None #' set to your own server to server api key. Cfr GoogleDevelopers Console. Set to None if you're not interested in freebase search