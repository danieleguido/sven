#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sven.models import Corpus, Profile
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User

class CorpusTestCase(TestCase):
  def setUp(self):
  	self.user = User.objects.create_user(username='jacob', email='jacob@…', password='top_secret')
  	self.corpus = Corpus.objects.create(name=u'this is just a test')

  def test_user_has_profile(self):
   	# should exist the profile for the given user
   	pro = Profile.objects.get(user=self.user)
   	self.assertEqual(pro.json()['username'], 'jacob')
