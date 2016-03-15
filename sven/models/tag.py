#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sven import helpers
from django.db import models
from django.core.validators import RegexValidator

class Tag(models.Model):
  '''
  Clustering documents according to tag. A special tag category is actor.
  feel free to add tag type to this model ... :D
  '''
  FREE = 'fr' # i.e, no special category at all
  ACTOR = 'ac'
  INSTITUTION = 'in'
  TYPE_OF_MEDIA = 'tm'
  PLACE = 'pl'

  ALCHEMY = {
    'City':'Ci'
  }
  
  TYPE_CHOICES = (
    (FREE, 'tags'),
    (TYPE_OF_MEDIA, 'type_of_media'),
    (ACTOR, 'actor'),
    (INSTITUTION, 'institution'),
    (PLACE, 'place'),
  )

  OEMBED_PROVIDER_NAME = 'OP' #tag specify an oembed field...
  OEMBED_TITLE = 'OT' #tag specify an oembed field...
  OEMBED_URL = 'OU'
  OEMBED_THUMBNAIL_URL = 'OH'
  OEMBED_VIDEO_ID = 'OI'
  OEMBED_HEIGHT = 'Oh'
  OEMBED_WIDTH = 'Ow'

  TYPE_OEMBED_CHOICES = (
    (OEMBED_PROVIDER_NAME, 'oembed_provider_name'),
    (OEMBED_TITLE, 'oembed_title'),
    (OEMBED_URL, 'oembed_url'),
    (OEMBED_THUMBNAIL_URL, 'oembed_thumbnail_url'),
    (OEMBED_VIDEO_ID, 'oembed_video_id'),
    (OEMBED_HEIGHT, 'oembed_height'),
    (OEMBED_WIDTH, 'oembed_width'),
  )

  name   = models.CharField(max_length=128) # e.g. 'Mr. E. Smith'
  corpus = models.ForeignKey('Corpus')
  slug   = models.SlugField(max_length=128, unique=True) # e.g. 'mr-e-smith'
  type   = models.CharField(max_length=32, validators=[
              RegexValidator(r'^[0-9a-z-A-Z\s]*$',
                'Only 0-9 are allowed.',
                'Invalid Number'
              ),
           ], default=FREE) # e.g. 'actor' or 'institution'


  def save(self, **kwargs):
    if self.pk is None:
      self.slug = helpers.uuslug(model=Tag, instance=self, value=self.name)
    super(Tag, self).save()


  @staticmethod
  def search(query):
    argument_list =[
      Q(name__icontains=query),
      Q(slug__icontains=query),   # add this only when there are non ascii chars in query. transform query into a sluggish field. @todo: prepare query as a slug
    ]
    return reduce(operator.or_, argument_list)

  def __unicode__(self):
    return "%s : %s"% (self.get_type_display(), self.name)


  def json(self, deep=False):
    d = {
      'id': self.id, # uniqueid
      'name': self.name,
      'slug': self.slug,
      'type': self.type
    }
    return d