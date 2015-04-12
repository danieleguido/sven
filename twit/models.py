#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re, tweepy

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from sven.models import Document, Corpus
from sven.distiller import gooseapi



class Account(models.Model):
  '''
  Describe a twitter account.
  It associate a twit to one or more corpus. Whenever a new document is found, 
  it will be duplicated for the different corpora. However, we keep trace.
  '''
  url = models.URLField(unique=True, max_length=128) #// the account url
  name = models.CharField(max_length=128, null=True, blank=True)

  abstract = models.TextField(null=True, blank=True)

  date_created = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  documents = models.ManyToManyField(Document, related_name='twitters', null=True, blank=True)



  def todolist(self):
    '''
    return a list of urls object to be scraped. Along with them, some info.
    '''
    todos = []

    auth = tweepy.OAuthHandler(
      settings.TWITTER_CONSUMER_KEY,
      settings.TWITTER_CONSUMER_SECRET
    )
    auth.set_access_token(
      settings.TWITTER_ACCESS_TOKEN,
      settings.TWITTER_ACCESS_TOKEN_SECRET
    )

    tapi = tweepy.API(auth)

    self.name = Account.get_twitter_account(self.url)
    
    if self.name is None:
      return None

    public_tweets = tapi.user_timeline(self.name)

    for tweet in public_tweets:
      urls = [t['expanded_url'] for t in tweet.entities[u'urls']]

      if len(urls) > 0:
        author = tweet.author.screen_name
        date = tweet.created_at

        for url in urls:
          todos.append({
            'date': date,
            'author': author,
            'url': url
          })

    return todos



  @staticmethod
  def get_twitter_account(url):
    name_match = re.search(r'twitter.com\/([A-Za-z0-9_]*)\/?$', url)
    if name_match is None:
      return None
    else:
      return name_match.group(1)
