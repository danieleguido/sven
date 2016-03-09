#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sven.models import Corpus, Profile
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User

class DocumentTextTest(TestCase):
  def setUp(self):
    # Every test needs access to the request factory.
    self.user, created = User.objects.get_or_create(
      username='jacob', email='jacob@…', password='top_secret')
    self.corpus, created = Corpus.objects.get_or_create(name=u'----test----')
    self.corpus.owners.add(self.user) # adding corpus to user


  def test_save_content(self):
    '''
    save a custom utf8 content string a document
    '''
    document = Document(corpus=self.corpus, name=u'custom text')
    document.save() # set_text use slug property...
    document.set_text(u'Mary had a little lamb.'.encode('UTF-8'))
    
    self.assertEqual(document.text(), u'Mary had a little lamb.'.encode('UTF-8'))


