#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pattern.en, pattern.fr

from pattern.search import search

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase

from sven.distiller import distill, EN_STOPWORDS, FR_STOPWORDS
from sven.models import Segment, Corpus, Document

from django.test.client import RequestFactory
import glue.api


class OSTest(TestCase):
  def test_permissions(self):
    cond = settings.MEDIA_ROOT is not None and os.path.exists(settings.MEDIA_ROOT)
    self.assertEqual(cond, True)



class CorpusTest(TestCase):
  def setUp(self):
    # Every test needs access to the request factory.
    self.factory = RequestFactory()
    self.user = User.objects.create_user(
      username='jacob', email='jacob@…', password='top_secret')
    self.admin = User(
      username='jacob_admin', email='jacob@…', password='top_secret', is_staff=True)
    self.corpus, created = Corpus.objects.get_or_create(name=u'----test----')


  def test_create_corpus(self):
    user = self.user

    corpus = self.corpus
    corpus.save()
    corpus.owners.add(user)
    corpus.save()
    
    self.assertEqual(corpus.slug, u'-test-')


  def test_get_corpus_via_glue(self):
    request = self.factory.get('/glue/sven/corpus/')
    request.user = self.admin

    response = glue.api.get_objects(request, 'sven', 'corpus')
    self.assertEqual('%s' % response, 'Content-Type: application/json\r\n\r\n{"status": "ok", "meta": {"total_count": 1, "module": "sven.models.Corpus", "user": "jacob_admin", "action": "get_objects", "model": "Corpus", "method": "GET"}, "objects": [{"pk": 1}]}')



class DocumentTest(TestCase):
  def test_create_document(self):
    user = User(username=u'new-user')
    user.save()

    corpus = Corpus(name=u'----test----')
    corpus.save()
    corpus.owners.add(user)
    corpus.save()

    # add a dummy raw document, txt
    document = Document(corpus=corpus)
    document.raw.save('test.txt', ContentFile(u'Mary had a little lamb.'.encode('UTF-8')), save=False)
    document.save()
    print document.text()
    print document.mimetype
    self.assertEqual(True, True)



class SegmentTests(TestCase):
  def test_save_segments(self):
    segments_en = distill("Mary had a little lamb and it was really gorgeous. None. Mary had a little lamb and it was really gorgeous. None.", language='en', query='NP')
   
    for i,(match, lemmata) in enumerate(segments_en):
      s, created = Segment.objects.get_or_create(content=match, lemmata=lemmata, cluster=lemmata, language='en')

    self.assertEqual(Segment.objects.count(), 3)



class DistillerTests(TestCase):
  def test_distill(self):
    '''
    test distill function with a default text
    '''
    segments_en = distill("Mary had a little lamb and it was really gorgeous. None.")
    segments_fr = distill("Mary avait un agneau et il etait vraiment sympa. Personne.", language="fr", stopwords=FR_STOPWORDS)

    self.assertEqual(segments_en + segments_fr, [
      (u'Mary', u'mary'),
      (u'a little lamb', u'lamb-little'),
      (u'None', u'none'),
      (u'Mary', u'mary'),
      (u'un agneau et il', u'agneau'),
      (u'Personne', u'personne')
    ])


  def test_parse_sentences(self):
    texts = [
      pattern.en.Text(pattern.en.parse("Mary had a little lamb and it was really gorgeous. None.",lemmata=True)),
      pattern.fr.Text(pattern.fr.parse("Mary avait un agneau et il etait vraiment sympa. Personne.",lemmata=True))
    ]

    nps = []
    
    for text in texts:
      for sentence in text:
        for match in search('NP', sentence):
          for word in match.words:
            nps.append(word.lemma)

    self.assertEqual(nps, [u'mary', u'a', u'little', u'lamb', u'it', u'none', u'mary', u'un', u'agneau', u'et', u'il', u'personne'])