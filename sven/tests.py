#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json
import pattern.en, pattern.fr

from pattern.search import search

from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.test import TestCase

from sven.distiller import distill, EN_STOPWORDS, FR_STOPWORDS
from sven.models import helper_truncatesmart
from sven.models import Segment, Corpus, Document, Job, Document_Segment, Tag

from django.test.client import RequestFactory
import glue.api
import sven.api



class HelpersTest(TestCase):
  '''
  This class test helper function in models.py
  '''
  def test_truncatesmart(self):
    v1 = helper_truncatesmart('This class test helper function in models.py', 25)
    v2 = helper_truncatesmart('This class test helper function in models.py', 125)
    print len(v1), len(v2), 
    self.assertEqual(len(v1) < 28, True)
    self.assertEqual(len(v2), len('This class test helper function in models.py'))



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

    self.assertEqual(jresponse['meta']['action'], u'sven.api.corpus')
    self.assertEqual(jresponse['meta']['method'], u'DELETE')
    self.assertEqual(jresponse['status'], u'ok')
   

  def text_delete_all_corpora(self):
    Corpus.objects.delete()
    self.assertEqual(0, Corpus.objects.count())


  def test_create_stopword(self):
    '''
    Create empty stopwords file. (small text files)
    '''
    stopwords = self.corpus.get_stopwords() # empty string
    self.corpus.set_stopwords(contents=[u'Hey', u'Alleluya'])
    self.corpus.set_stopwords(contents=[u'English Hey', u'English Alleluya'], language='en')
    stopwords = self.corpus.get_stopwords()
    #print stopwords
    en_stopwords = self.corpus.get_stopwords(language='en')
    self.assertEqual(stopwords, [u'Hey', u'Alleluya'])
    self.assertEqual(en_stopwords, [u'English Hey', u'English Alleluya'])


  def test_upload_metadata_csv(self):
    '''
    copy the csv file directly under the contents/csv dir (cfr sven.settings)
    each file has its own timestamp.
    This function also test the creation of corpus folder under the contents dir.
    '''
    self.factory = RequestFactory()
    with open(os.path.join(settings.BASE_DIR, 'contents/test.metadata.csv')) as fp:
      request = self.factory.post(reverse('sven_api_import_corpus_documents', args=[self.corpus.pk]), {'file': fp})
      
      # attach user to corpus
      self.corpus.owners.add(self.user)
      self.corpus.save()
      request.user = self.user

      response = sven.api.import_corpus_documents(request, corpus_pk=self.corpus.pk)
      jresponse = json.loads(response.content)

      self.assertEqual('object' in jresponse, True)



class DocumentTextTest(TestCase):
  def setUp(self):
    # Every test needs access to the request factory.
    self.user = User.objects.create_user(
      username='jacob', email='jacob@…', password='top_secret')
    self.corpus, created = Corpus.objects.get_or_create(name=u'----test----')
    self.corpus.owners.add(self.user) # adding two documents


  def test_save_content(self):
    '''
    save a custom utf8 content string a document
    '''
    document = Document(corpus=self.corpus, name=u'custom text')
    document.save() # set_text use slug property...
    document.set_text(u'Mary had a little lamb.'.encode('UTF-8'))
    
    self.assertEqual(document.text(), u'Mary had a little lamb.'.encode('UTF-8'))



class DocumentTest(TestCase):
  def setUp(self):
    # Every test needs access to the request factory.
    self.user = User.objects.create_user(
      username='jacob', email='jacob@…', password='top_secret')
    self.corpus, created = Corpus.objects.get_or_create(name=u'----test----')
    self.corpus.owners.add(self.user) # adding two documents


  def test_upload_file(self):
    self.factory = RequestFactory()
    with open(os.path.join(settings.BASE_DIR, 'contents/test.pdf')) as fp:
      request = self.factory.post(reverse('sven_api_document_upload', args=[self.corpus.pk]), {'file': fp})
      request.user = self.user

      # admin is among owners
      response = sven.api.document_upload(request, corpus_pk=self.corpus.pk)
      jresponse = json.loads(response.content)
      print jresponse
  

  def test_create_whoosh(self):
    '''
    Create whoosh index. Normally we should add here a file as a test. @todo
    '''
    index = Document.get_whoosh()
    self.assertEqual(os.path.exists(settings.WHOOSH_PATH), True)


  def test_create_document_having_datetime(self):
    # test tag creation, language and date. Note: doc only date should only have date.. 
    doc_with_tag_in_its_name = Document(corpus=self.corpus, name=u'rights  -  policy  - advocacy__EN_20140417_PC230')
    doc_with_tag_in_its_name.save()
    self.assertEqual(doc_with_tag_in_its_name.name, 'PC230')
    self.assertEqual(doc_with_tag_in_its_name.language, 'en')
    self.assertEqual(doc_with_tag_in_its_name.tags.count(), 3)

    doc_with_tag_in_its_name_but_unvalid_title = Document(corpus=self.corpus, name=u'rights  -  policy  - advocacy__EN_20140417_')
    doc_with_tag_in_its_name_but_unvalid_title.save()
    self.assertEqual(doc_with_tag_in_its_name_but_unvalid_title.name, u'rights  -  policy  - advocacy__EN_20140417_')
    self.assertEqual(doc_with_tag_in_its_name_but_unvalid_title.language, 'en')
    self.assertEqual(doc_with_tag_in_its_name_but_unvalid_title.tags.count(), 3)

    doc_with_only_date_in_its_name = Document(corpus=self.corpus, name=u'N-L_d_2014.03.05_') # because title here is null
    doc_with_only_date_in_its_name.save()
    self.assertEqual(doc_with_only_date_in_its_name.date.isoformat(), '2014-03-05T00:00:00+00:00')
    self.assertEqual(doc_with_only_date_in_its_name.language, '')
    self.assertEqual(doc_with_only_date_in_its_name.tags.count(), 0)
    #print doc_with_tag_in_its_name_but_unvalid_title.name, doc_with_tag_in_its_name.name, doc_with_tag_in_its_name.language,doc_with_only_date_in_its_name.language, doc_with_only_date_in_its_name.name
    


  def test_create_document(self):
    # add a dummy raw document, txt
    document = Document(corpus=self.corpus)
    document.raw.save('test.txt', ContentFile(u'Mary had a little lamb.'.encode('UTF-8')), save=False)
    document.save()
    self.assertEqual(document.text(), u'Mary had a little lamb.'.encode('UTF-8'))
    



  def test_create_document_from_pdf(self):
    from django.core.files import File
    f = open(os.path.join(settings.BASE_DIR, 'contents/test.pdf')) # Open an existing file using Python's built-in open()
    p = File(f)
    doc = Document(corpus=self.corpus, name=u"unnamed")
    doc.raw.save('test_copy.pdf', p, save=False)
    doc.save()
    
    self.assertEqual(doc.mimetype, 'application/pdf')
    #print document.text()



  def test_computate_tf(self):
    from pattern.vector import LEMMA, Document as PatternDocument



    doc_a = Document(corpus=self.corpus)
    doc_a.raw.save('alice_a.txt', ContentFile(u' She follows it down a rabbit hole when suddenly she falls a long way to a curious hall with many locked doors of all sizes. She finds a small key to a door too small for her to fit through, but through it she sees an attractive garden.'.encode('UTF-8')), save=False)
    doc_a.save()

    doc_b = Document(corpus=self.corpus)
    doc_b.raw.save('alice_b.txt', ContentFile(u' She then discovers a bottle on a table labelled "DRINK ME," the contents of which cause her to shrink too small to reach the key which she has left on the table. She eats a cake with "EAT ME" written on it in currants as the chapter closes.'.encode('UTF-8')), save=False)
    doc_b.save()

    try:
      self.corpus.tfidf()
    except Exception, e:
      print e
      
    segments_a = distill(content=doc_a.text())
    
    for i,(match, lemmata, tf, wf) in enumerate(segments_a):
      seg, created = Segment.objects.get_or_create(content=match, lemmata=lemmata, cluster=lemmata, language=settings.EN, corpus=self.corpus)
      dos, created = Document_Segment.objects.get_or_create(document=doc_a, segment=seg, tf=tf, wf=wf)

    segments_b = distill(content=doc_b.text())

    for i,(match, lemmata, tf, wf) in enumerate(segments_b):
      seg, created = Segment.objects.get_or_create(content=match, lemmata=lemmata, cluster=lemmata, language=settings.EN, corpus=self.corpus)
      dos, created = Document_Segment.objects.get_or_create(document=doc_b, segment=seg, tf=tf, wf=wf)

    self.corpus.tfidf()
    pass



class WebServicesTest(TestCase):
  def setUp(self):
    # Every test needs access to the request factory.
    self.user = User.objects.create_user(
      username='jacob', email='jacob@…', password='top_secret')
    self.corpus, created = Corpus.objects.get_or_create(name=u'----test----')
    self.corpus.owners.add(self.user) # adding two documents


  def test_oembed_services(self):
    import micawber
    mic = micawber.bootstrap_basic()
    you = mic.request('https://www.youtube.com/watch?v=GGyLP6R4HTE') # youtube
    vim = mic.request('http://vimeo.com/17081933') # vimeo


    print self.assertEqual(you['provider_name'], u'YouTube')
    print self.assertEqual(vim['provider_name'], u'Vimeo')

    document = Document(corpus=self.corpus, name=u'N-L_FR_20140305_.txt')
    document.mimetype = "text/html"
    document.save()

    t1, created = Tag.objects.get_or_create(type=Tag.OEMBED_PROVIDER_NAME, name=vim['provider_name'])
    t1, created = Tag.objects.get_or_create(type=Tag.OEMBED_TITLE, name=vim['title'])
    t2, created = Tag.objects.get_or_create(type=Tag.OEMBED_THUMBNAIL_URL, name=vim['thumbnail_url'])  

  def test_create_document_having_url(self):
    document = Document(corpus=self.corpus, name=u'tunisian-youth')
    document.mimetype = "text/html"
    document.url = 'http://mideastposts.com/middle-east-politics-analysis/tunisian-youth-turned-politics-effect-change'
    
    document.save()
    print document.text()



class DocumentInfoTest(TestCase):
  def setUp(self):
    # Every test needs access to the request factory.
    self.user = User.objects.create_user(
      username='jacob', email='jacob@…', password='top_secret')
    self.corpus, created = Corpus.objects.get_or_create(name=u'----test----')
    self.corpus.owners.add(self.user) # adding two documents
    

  def test_save_document_info(self):
    '''
    test post_save receiver for DocumentInfo model
    '''
    doc = Document(corpus=self.corpus, name=u'docuemntinfotest.txt')
    doc.save()
    doc.info.date_textified = doc.info.date_last_modified
    print doc.info.date_textified
    self.assertEqual(doc.info.pk, 1)



class SegmentTests(TestCase):
  def setUp(self):
    # Every test needs access to the request factory.
    self.user = User.objects.create_user(
      username='jacob', email='jacob@…', password='top_secret')
    self.corpus, created = Corpus.objects.get_or_create(name=u'----test----')
    self.corpus.owners.add(self.user)


  def test_save_segments(self):
    segments_en = distill("Mary had a little lamb and it was really gorgeous. None. Mary had a little lamb and it was really gorgeous. None.", language='en', query='NP')
   
    for i,(match, lemmata, tf, wf) in enumerate(segments_en):
      s, created = Segment.objects.get_or_create(content=match, lemmata=lemmata, cluster=lemmata, language='en', corpus=self.corpus)

    self.assertEqual(Segment.objects.count(), 3)



class DistillerTests(TestCase):
  def test_distill(self):
    '''
    test distill function with a default text
    '''
    segments_en = distill("Mary had a little lamb and it was really gorgeous. None.")
    segments_fr = distill("Mary avait un agneau et il etait vraiment sympa. Personne.", language="fr", stopwords=FR_STOPWORDS)
    # print segments_en + segments_fr
    self.assertEqual(segments_en + segments_fr, [
      (u'Mary', u'mary', 0.25, 0.32192809488736235), (u'a little lamb', u'lamb little', 0.25, 0.32192809488736235), (u'None', u'none', 0.0, 0.0), (u'Mary', u'mary', 0.2, 0.2630344058337938), (u'un agneau et il', u'agneau', 0.2, 0.2630344058337938), (u'Personne', u'personne', 0.0, 0.0),
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


  def test_goose(self):
    from distiller import gooseapi
    article = gooseapi(url='http://www.nytimes.com/2013/08/18/world/middleeast/pressure-by-us-failed-to-sway-egypts-leaders.html?hp')
      #'http://mideastposts.com/middle-east-politics-analysis/tunisian-youth-turned-politics-effect-change')
    #self.assertEqual(article.title, u'Tunisia Revolution')
    print article.title
    print article.cleaned_text[:150]

    article = gooseapi(url='http://mideastposts.com/middle-east-politics-analysis/tunisian-youth-turned-politics-effect-change')
    print article.title
    print article.cleaned_text[:150]

    twit = gooseapi(url='https://twitter.com/IwatchTn')
    print twit.title
    print twit.cleaned_text



  def test_freebase(self):
    from distiller import freebase
    if settings.FREEBASE_KEY is not None:
      concepts = freebase(query='Bohain-en-Vermandois', lang='fr', api_key=settings.FREEBASE_KEY)
      
      if concepts is not None:
        for c in concepts:
          pass #print c


  def test_alchemyapi(self):
    from distiller import alchemyapi
    if settings.ALCHEMYAPI_KEY is not None:
      res = alchemyapi(api_key=settings.ALCHEMYAPI_KEY, text=u"Mary Cachasça had a little lamb and it was really gorgeous, in Paris.")
      #print res
      self.assertEqual(res['entities'][0]['type'], u'Person')


  def test_textrazor(self):
    from distiller import textrazor
    if settings.TEXTRAZOR_KEY is not None:
      res = textrazor(api_key=settings.TEXTRAZOR_KEY, text=u"Mary Cachasça had a little lamb and it was really gorgeous, in Paris.")
      print res['response']['entities'][0]['type']
      self.assertEqual(res['response']['entities'][0]['type'], [u'Person'])

  
  def test_goose(self):
    from distiller import gooseapi
    #article = gooseapi(url='http://www.nytimes.com/2013/08/18/world/middleeast/pressure-by-us-failed-to-sway-egypts-leaders.html?hp')
    #'http://mideastposts.com/middle-east-politics-analysis/tunisian-youth-turned-politics-effect-change')
    #self.assertEqual(article.title, u'Tunisia Revolution')
    #print article.title
    #print article.cleaned_text[:150]

    #article = gooseapi(url='http://mideastposts.com/middle-east-politics-analysis/tunisian-youth-turned-politics-effect-change')
    #print article.title
    #print article.cleaned_text[:150]

    #twit = gooseapi(url='https://twitter.com/nawaat')
    ##print "twitter account"
    #print twit.title
    #print twit.cleaned_text

    #yout = gooseapi(url='https://www.youtube.com/watch?v=OqlEgcC_XTo')
    #print "youtube account"
    #print yout.title
    #print yout.cleaned_text

    #youch = gooseapi(url='https://www.youtube.com/user/canadiantourism') useless
    #print "youtube channel"
    #print youch.title
    #print youch.cleaned_text
    

