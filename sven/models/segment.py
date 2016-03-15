#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sven import helpers
from django.conf import settings
from django.db import models
from sven.models import Corpus
from sven.models import Entity


class Segment( models.Model): 
  OUT = 'OUT'
  IN = 'IN'

  STATUS_CHOICES = (
    (OUT, u'exclude'),
    (IN, u'include'),
  )

  NP = 'NP'
  VP = 'VP'
  POS_CHOICES = (
    (NP, u'N phrase'),
    (VP, u'V phrase'),
  )

  content = models.CharField(max_length=128)
  lemmata = models.CharField(max_length=128)
  cluster = models.CharField(max_length=128) # index by cluster. Just to not duplicate info , e.g by storing them in a separate table. Later you can group them by cluster (to be indexed).

  entity  = models.ForeignKey(Entity, related_name="segments", null=True, blank=True) # disambiguated entity, alternative to cluster. Indeed the same cluster may have different entity according to the context

  corpus    = models.ForeignKey(Corpus, related_name="segments") # corpus specific [sic]
  language  = models.CharField(max_length=2, choices=settings.LANGUAGE_CHOICES)
  status    = models.CharField(max_length=3, choices=STATUS_CHOICES, default=IN)
  
  partofspeech = models.CharField(max_length=3, choices=POS_CHOICES)


  def __unicode__(self):
    return '%s [%s]' % (self.content, self.lemmata)


  def json(self, deep=False):
    d = {
      'id': self.id,
      'content': self.content,
      'cluster': self.cluster 
    }
    return d


  class Meta:
    unique_together = ('content', 'corpus', 'partofspeech')