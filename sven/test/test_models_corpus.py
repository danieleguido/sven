#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from sven.models import Corpus, Profile
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

import sven.api.corpus

class CorpusTestCase(TestCase):
  def setUp(self):
    self.factory = RequestFactory()
    self.user = User.objects.create_user(username='jacob', email='jacob@…', password='top_secret')
    self.corpus = Corpus.objects.create(name=u'this is just a test')


  def test_user_has_profile(self):
    # should exist the profile for the given user
    pro = Profile.objects.get(user=self.user)
    self.assertEqual(pro.json()['username'], 'jacob')

  def test_get_items(self):
    request = self.factory.get(reverse('sven_api_corpora'))
    request.user = self.user
    request.method = 'GET'
    # request.user = self.user
    response = sven.api.corpus.items(request)
    self.assertEqual(0, len(json.loads(response.content)['objects']))

    self.corpus.owners.add(self.user)

    self.corpus.owners.add(self.user)
    response = sven.api.corpus.items(request)
    self.assertEqual(1, len(json.loads(response.content)['objects']))