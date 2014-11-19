#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys, site

site.addsitedir('/home/user/.virtualenvs/sven/lib/python2.7/site-packages') #

path = '/home/user/sven' # sven path
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'sven.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
