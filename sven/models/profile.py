#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sven import helpers
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

class Profile(models.Model):
  user    = models.OneToOneField(User)
  bio     = models.TextField(null=True, blank=True)
  picture = models.URLField(max_length=160, blank=True, null=True)
  date_created = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  class Meta:
    app_label="sven"

  def json(self, deep=False):
    d = {
      'id': self.id,
      'bio_raw': self.bio,
      'bio': self.bio,
      'picture': self.picture,
      'username': self.user.username,
      'firstname': self.user.first_name,
      'lastname': self.user.last_name,
      'date_created': self.date_created.isoformat(),
      'date_last_modified': self.date_last_modified.isoformat() if self.date_last_modified else None,
    }
    return d


  def save(self, **kwargs):
    if self.pk is None or len(self.picture) == 0:
      try:
        self.picture = helpers.palette()[0]['imageUrl']
      except urllib2.URLError, e:
        logger.error(e)
    super(Profile, self).save()


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
  if created:
    pro = Profile(user=instance, bio="")
    pro.save()