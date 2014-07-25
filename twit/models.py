#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from sven.models import Document, Corpus


class Twit(models.Model):
  '''
  Describe a twitter account
  '''
  url = models.URLField(unique=True, max_length=128) #// the account url
  name = models.CharField(max_length=128, null=True, blank=True)

  abstract = models.TextField(null=True, blank=True)

  date_created = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  corpus = models.ManyToManyField(Corpus, related_name='twitters') # account twitters
  documents = models.ManyToManyField(Document, related_name='twitters')


  @staticmethod
  def get_twitter_account(url):
    name_match = re.search(r'\/([A-Za-z0-9_]*)\/?$', url)
    if name_match is None:
      return None
    else:
      return name_match.group(1)
