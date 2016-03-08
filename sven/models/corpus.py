#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from sven import helpers
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings


class Corpus(models.Model):
  name = models.CharField(max_length=32)
  slug = models.CharField(max_length=32, unique=True)
  color = models.CharField(max_length=6, blank=True)

  date_last_modified = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)

  owners = models.ManyToManyField(User, related_name="corpora", blank=False)

  class Meta:
    verbose_name_plural = 'corpora'


  def get_path(self):
    return os.path.join(settings.MEDIA_ROOT, self.slug)


  def save(self, **kwargs):
    self.slug = helpers.uuslug(model=Corpus, instance=self, value=self.name)
    path = self.get_path()
    if not os.path.exists(path):
      os.makedirs(path)

    if self.pk is None or len(self.color) == 0:
      self.color = helpers.colour()[0]['hex']
      
    super(Corpus, self).save()


  def __unicode__(self):
    return '%s [%s]' % (self.name, self.slug)
