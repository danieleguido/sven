#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json
import pattern.en, pattern.fr

from pattern.search import search

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.test import TestCase

from sven.distiller import distill, EN_STOPWORDS, FR_STOPWORDS
from sven.models import Segment, Corpus, Document, Job, Document_Segment

from django.test.client import RequestFactory
import glue.api
import sven.api


class OSTest(TestCase):
  def test_permissions(self):
    cond = settings.MEDIA_ROOT is not None and os.path.exists(settings.MEDIA_ROOT)
    self.assertEqual(cond, True)



class JobTest(TestCase):
  def test_start_job_harvest(self):
    # Every test needs access to the request factory.
    corpus, created = Corpus.objects.get_or_create(name=u'----test----')
    job = Job.start(corpus=corpus, command='harvest')

    # stop job
    job.stop()
    


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


  def test_delete_corpus(self):
    request = self.factory.get(reverse('sven_api_corpus', args=[self.corpus.pk]))
    request.method='DELETE'
    request.user = self.admin

    # admin is among owners
    response = sven.api.corpus(request, pk=self.corpus.pk)
    jresponse = json.loads(response.content)

    self.assertEqual('%s-%s-%s' % (jresponse['meta']['action'], jresponse['meta']['method'], jresponse['status']), 'corpus-DELETE-ok')


  def text_delete_all_corpora(self):
    Corpus.objects.delete()
    self.assertEqual(0, Corpus.objects.count())



class DocumentTest(TestCase):
  def setUp(self):
    # Every test needs access to the request factory.
    self.user = User.objects.create_user(
      username='jacob', email='jacob@…', password='top_secret')
    self.corpus, created = Corpus.objects.get_or_create(name=u'----test----')
    self.corpus.owners.add(self.user)

    # adding two documents



  def test_create_document_having_datetime(self):
    document = Document(corpus=self.corpus, name=u'N-L_FR_20140305_.txt')
    document.save()
    self.assertEqual(document.date.isoformat(), '2014-03-05T00:00:00+00:00')


  def test_create_document(self):
    # add a dummy raw document, txt
    document = Document(corpus=self.corpus)
    document.raw.save('test.txt', ContentFile(u'Mary had a little lamb.'.encode('UTF-8')), save=False)
    document.save()
    self.assertEqual(document.text(), u'Mary had a little lamb.'.encode('UTF-8'))


  def test_computate_tf(self):
    from pattern.vector import LEMMA, Document as PatternDocument

    doc_a = Document(corpus=self.corpus)
    doc_a.raw.save('alice_a.txt', ContentFile(u' She follows it down a rabbit hole when suddenly she falls a long way to a curious hall with many locked doors of all sizes. She finds a small key to a door too small for her to fit through, but through it she sees an attractive garden.'.encode('UTF-8')), save=False)
    doc_a.save()

    doc_b = Document(corpus=self.corpus)
    doc_b.raw.save('alice_b.txt', ContentFile(u' She then discovers a bottle on a table labelled "DRINK ME," the contents of which cause her to shrink too small to reach the key which she has left on the table. She eats a cake with "EAT ME" written on it in currants as the chapter closes.'.encode('UTF-8')), save=False)
    doc_b.save()

    content_a = doc_a.text()

    segments_a = distill(content=content_a)

    for i,(match, lemmata, tf, wf) in enumerate(segments_a):
      seg, created = Segment.objects.get_or_create(content=match, lemmata=lemmata, cluster=lemmata, language=settings.EN)
      dos, created = Document_Segment.objects.get_or_create(document=doc_a, segment=seg, tf=tf, wf=wf)

    pass




class SegmentTests(TestCase):
  def test_save_segments(self):
    segments_en = distill("Mary had a little lamb and it was really gorgeous. None. Mary had a little lamb and it was really gorgeous. None.", language='en', query='NP')
   
    for i,(match, lemmata, tf, wf) in enumerate(segments_en):
      s, created = Segment.objects.get_or_create(content=match, lemmata=lemmata, cluster=lemmata, language='en')

    self.assertEqual(Segment.objects.count(), 3)



class DistillerTests(TestCase):
  def test_distill(self):
    '''
    test distill function with a default text
    '''
    segments_en = distill("Mary had a little lamb and it was really gorgeous. None.")
    segments_fr = distill("Mary avait un agneau et il etait vraiment sympa. Personne.", language="fr", stopwords=FR_STOPWORDS)
    print segments_en + segments_fr
    self.assertEqual(segments_en + segments_fr, [
      (u'Mary', u'mary', 0.25, 0.32192809488736235), (u'a little lamb', u'lamb-little', 0.25, 0.32192809488736235), (u'None', u'none', 0.0, 0.0), (u'Mary', u'mary', 0.2, 0.2630344058337938), (u'un agneau et il', u'agneau', 0.2, 0.2630344058337938), (u'Personne', u'personne', 0.0, 0.0),

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