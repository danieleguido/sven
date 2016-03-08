#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sven.models import Profile
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User

class ProfileTestCase(TestCase):
  def setUp(self):
  	self.user = User.objects.create_user(username='jacob', email='jacob@…', password='top_secret')

  def test_user_has_profile(self):
   	# should exist the profile for the given user
   	pro = Profile.objects.get(user=self.user)
   	self.assertEqual(pro.json()['username'], 'jacob')
