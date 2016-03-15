#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.test import TestCase

import sven.api

class SerializerTest(TestCase):
  def setUp(self):
    # Every test needs access to the request factory.
    self.factory = RequestFactory()
    self.user = User.objects.create_user(
      username='jacob', email='jacob@…', password='top_secret')

  def test_echo(self):
    print reverse('sven_api_echo')
    request = self.factory.get(reverse('sven_api_echo'))
    request.method = 'GET'
    # request.user = self.user
    response = sven.api.echo(request)
    print response.content
