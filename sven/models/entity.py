#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.db import models


class Entity(models.Model):
  '''
  dbpedia or viaf entity, uniqueness guaranteed on URL field
  '''
  FREE   = ''
  PERSON = 'Per'
  PLACE  = 'Pla'
  ORGANISATION = 'Org'

  TYPE_CHOICES = (
    (PERSON, 'person'),
    (PLACE, 'place'),
    (ORGANISATION, 'organisation'),
  )

  content = models.CharField(max_length=128)
  url     = models.URLField(unique=True)
  type    = models.CharField(max_length=3, choices=TYPE_CHOICES, default=FREE) 

