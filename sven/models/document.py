#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, codecs

from sven import helpers
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from sven.models import Corpus, Segment

def get_document_path(instance, filename):
  '''
  return a custom upload folder based on corpus path.
  '''
  return os.path.join(instance.corpus.get_path(),filename)



class Document(models.Model):
  DOCUMENT_ABSTRACT_PLACEHOLDER = '...'

  name = models.CharField(max_length=128)
  slug = models.CharField(max_length=128, unique=True)
  abstract = models.CharField(max_length=160,  blank=True, null=True) # sample taken from .text() transformation 
  corpus = models.ForeignKey(Corpus, related_name='documents')
  
  language  = models.CharField(max_length=2, choices=settings.LANGUAGE_CHOICES)

  raw  = models.FileField(upload_to= get_document_path , blank=True, null=True, max_length=200)
  mimetype = models.CharField(max_length=100, blank=True, null=True, default='empty')



  date = models.DateTimeField(blank=True, null=True)
  date_created = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)
  
  url = models.URLField(blank=True, null=True, max_length=255) # external url to be boilerplated

  # segments = models.ManyToManyField(Segment, through="Document_Segment", blank=True, null=True)
  # tags = models.ManyToManyField(Tag, blank=True, null=True, related_name='tagdocuments')

  def __unicode__(self):
    return '%s [%s]' % (self.name, self.slug)

  def text(self):
    '''
    Get utf8 text content of the file. If the document is of type text/html
    '''
    content = ''

    if self.mimetype is None:
      content = "" # not yet ready ... Empty string
    elif self.mimetype == 'text/plain' and self.raw and os.path.exists(self.raw.path):
        with codecs.open(self.raw.path, encoding='utf-8', mode='r') as f:
          content = f.read()

    else: #document which need textification
      textified = '%s.txt' % self.raw.path if self.raw else '%s/%s.txt' % (self.corpus.get_path(), self.slug)
      
      if os.path.exists(textified):
        with codecs.open(textified, encoding='utf-8', mode='r') as f:
          content = f.read()

      else: # content needs to b created
        if self.mimetype == "application/pdf":
          content = pdftotext(self.raw.path)
          with codecs.open(textified, encoding='utf-8', mode='w') as f:
            f.write(content)
        elif self.url is not None:
          try:
            goo = gooseapi(url=self.url) # use gooseapi to extract text content from html
          except urllib2.HTTPError,e:
            # logger.error('HTTPError received while goosing %s: %s' % (self.url, e))
            content = ''
          except IOError, e:
            pass
            # logger.error('IOError received while goosing %s: %s' % (self.url, e))
          else:
            content = goo.cleaned_text
            with codecs.open(textified, encoding='utf-8', mode='w') as f:
              f.write(content)
        else:
          content = '' #%s does not have a text associed. %s' % (self.mimetype, textified)
        # exitsts text translations?
        
        # store whoosh, only if contents needs to be created. not that store update document content in index
        if len(content):
          self.store(content)

    if not self.language or not self.abstract or self.abstract == Document.DOCUMENT_ABSTRACT_PLACEHOLDER:
      import langid
      self.abstract = helpers.truncatesmart(content, 150)
      language, probability = langid.classify(content[:255])
      self.language = language
      self.save()
    
    # content = dry(content)

    if not len(content):
      print 'Unable to find some text content for document id:%s' % (self.id)
      # logger.error('Unable to find some text content for document id:%s' % (self.id))
    return content


  def set_text(self, content):
    print 'self mimetype document', self.mimetype, self.raw
    if self.mimetype == 'text/plain' and self.raw is not None:
      textified = self.raw.path
    else:
      textified = '%s.txt' % self.raw.path if self.raw else '%s/%s.txt' % (self.corpus.get_path(), self.slug)

    with codecs.open(textified, encoding='utf-8', mode='w') as f:
      f.write(content)

    return content



class Document_Segment( models.Model ):
  '''
  custom document segment relationship
  '''
  document = models.ForeignKey(Document, related_name="document_segments")
  segment = models.ForeignKey(Segment, related_name="document_segments")

  tf = models.FloatField(default=0) # term normalized frequency of the stemmed version of the segment
  tfidf = models.FloatField( default=0) # inversed term calculated according to the document via the stemmed version
  wf = models.FloatField(default=0) # sublinear tf scaling (normalized on logarithm) = log(tf) if tf > 0
  tfidf = models.FloatField( default=0) # inversed term calculated according to the document via the stemmed version

  class Meta:
    unique_together = ("segment", "document")

  def json(self, deep=False):
    d = self.segment.json()
    d.update({
      'tf': self.tf,
      'wf': self.wf,
      'num_clusters': self.num_clusters
    })
    return d

