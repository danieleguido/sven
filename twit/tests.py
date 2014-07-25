#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.test import TestCase

from twit.models import Twit


class TwitTests(TestCase):
  def test_modification_date(self):
    t, created = Twit.objects.get_or_create(url='https://twitter.com/nawaat')
    import time
    d1 = t.date_last_modified
    time.sleep(2)
    t.save()
    d2 = t.date_last_modified
    d = d2 - d1
    self.assertEquals(d.total_seconds > 0, True)

  def test_get_twitter_account(self):
    t, created = Twit.objects.get_or_create(url='https://twitter.com/nawaat')
    account = Twit.get_twitter_account(url=t.url)
    self.assertEquals(account, 'nawaat')


class TwitterTests(TestCase):
  def setUp(self):
    if settings.TWITTER_CONSUMER_KEY is not None:
      import tweepy # cfr tweepy api references
      auth = tweepy.OAuthHandler(
        settings.TWITTER_CONSUMER_KEY,
        settings.TWITTER_CONSUMER_SECRET
      )
      auth.set_access_token(
        settings.TWITTER_ACCESS_TOKEN,
        settings.TWITTER_ACCESS_TOKEN_SECRET
      )

      self.api = tweepy.API(auth)
    

  def __test_twitterapi_having_links(self):
    '''
    Extract text from twits. Auto add as documents ?
    enable only for specific tests!!
    '''
    from distiller import gooseapi, alchemyapi_url
    if self.api:
      public_tweets = self.api.user_timeline('nawaat')
      for tweet in public_tweets:
        urls = [t['expanded_url'] for t in tweet.entities[u'urls']]
        if len(urls) > 0:
          print tweet.created_at, 'by', tweet.author.screen_name
          for url in urls:
            twitter_url = gooseapi(url=url)
            print 'url: ', url
            print 'title: ',twitter_url.title
            print 'with goose: ', twitter_url.cleaned_text[:150] #first 50 chars, if any
            
            if settings.ALCHEMYAPI_KEY is not None:
              res = alchemyapi_url(api_key=settings.ALCHEMYAPI_KEY, url=url)
              print 'with alchemy: ',res['text'][:150]
      #print res
          print '---'
           # break at first



  def test_twitterapi(self):
    if self.api:
      public_tweets = self.api.user_timeline('nawaat')
      for tweet in public_tweets:
        print tweet.created_at, 'by', tweet.author.screen_name
        print 'hashtags', [t['text'] for t in tweet.entities[u'hashtags']] 
        urls = [t['expanded_url'] for t in tweet.entities[u'urls']]
        
        for i in urls:
          print 'url', i
        print tweet.text
        break