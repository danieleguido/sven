import os

DEBUG = True
ALLOWED_HOSTS = [] # change this according to the documentation

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SVEN_NAME = 'SVEN'
SECRET_KEY = 'your own generated secret key'

DB_ENGINE = 'django.db.backends.sqlite3'
DB_NAME = os.path.join(BASE_DIR, 'sqlite/db.sqlite3') # given as example

LANGUAGE_CODE = 'en-us'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

PYTHON_INTERPRETER = '/home/daniele/.virtualenvs/sven/bin/python' # mine, given as exemple. Cfr virtualenv doc.

ENABLE_CDN_SERVICES = False # set to true if you want to use CDN. This const will be used in templates

FREEBASE_KEY = None #' set to your own server to server api key. Cfr GoogleDevelopers Console. Set to None if you're not interested in freebase search
ALCHEMYAPI_KEY = None #' set to your own alchemy api key. Cfr <http://lchemyapi.com>. Set to None if you're not interested in alchemy api
TWITTER_CONSUMER_KEY = None
TWITTER_CONSUMER_SECRET =  None
TWITTER_ACCESS_TOKEN = None
TWITTER_ACCESS_TOKEN_SECRET = None