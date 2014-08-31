#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, csv, time, codecs, shutil, urllib2, logging, langid
from optparse import make_option
from datetime import datetime

from django.conf import settings
from django.db import transaction, connection
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from sven.models import Corpus, Document, Job, Document_Segment, Segment



logger = logging.getLogger("sven")



class Command(BaseCommand):
  '''
  usage type:
  
  python manage.py start_job --job=1 --cmd=test
  '''
  args = ''
  help = 'execute some job on corpus.'
  option_list = BaseCommand.option_list + (
    make_option('--job',
      action='store',
      dest='job_pk',
      default=False,
      help='corpus primary key'),

    make_option('--cmd',
        action='store',
        dest='cmd',
        default=False,
        help='manage.py command to be executed'),
  )


  def _test(self, job):
    job.completion = .2
    job.save()
    time.sleep(15)
    job.completion = .6
    job.save()
    time.sleep(15)
    job.completion = .8
    job.save()
    time.sleep(15)
  

  def _tfidf(self, job):
    import math
    from sven.distiller import dictfetchall

    number_of_documents = job.corpus.documents.count()
    number_of_segments  = job.corpus.segments.count()

    print number_of_documents

    print number_of_segments
    if number_of_documents == 0:
      raise Exception('not enough "documents" in corpus to perform tfidf')# @todo

    if number_of_segments == 0:
      raise Exception('not enough "segments" in corpus to perform tfidf')# @todo

    # 2. get all languages in corpus
    number_of_languages = job.corpus.segments.values('language').distinct()
    
    print "number_of_languages", number_of_languages
    # 3. start querying per language stats
    cursor = connection.cursor()

    step = 0;
    for i in number_of_languages:
      language = i['language']
      # get number of clusters per language to print completion percentage (can we save it if self.job exists)
      #clusters = self.segments.filter(language=language).values('cluster').annotate(Count('cluster'))
      #for c in clusters:
      #  print c['cluster'], c

      # distribution query. In how many document can a cluster be found?
      clusters = cursor.execute("""
        SELECT
          COUNT( DISTINCT ds.document_id ) as distribution, 
          s.language,
          s.cluster
        FROM `sven_document_segment` ds
        JOIN `sven_segment` s ON ds.segment_id = s.id
        JOIN `sven_document` d ON d.id = ds.document_id
        WHERE d.corpus_id = %s AND s.language = %s AND s.status = %s
        GROUP BY s.cluster
        ORDER BY distribution DESC, cluster ASC""", [
          job.corpus.id,
          language,
          Segment.IN
        ]
      )
      
      for i, cluster in enumerate(dictfetchall(cursor)):
        step = step+1
        print step
        
        with transaction.atomic():  
          # for each cluster, calculate df value inside the overall corpus.
          df = float(cluster['distribution'])/number_of_documents
          
          # group by cluster and update value for the document_segment table. TFIDF is specific for each couple.
          for ds in Document_Segment.objects.filter(segment__cluster=cluster['cluster'], segment__language=language):
            ds.tfidf = ds.tf * math.log(1/df) 
            ds.wfidf = ds.wf * math.log(1/df)
            print i, cluster['cluster'], df, ds.tf, ds.tfidf
            ds.save()

    

  def _harvest(self, job):
    from sven.distiller import distill, EN_STOPWORDS, FR_STOPWORDS, NL_STOPWORDS

    logger.debug('executing "harvest"...')
    
    docs = job.corpus.documents.all()
    total = docs.count()

    logger.debug('corpus %s contains %s documents' % (job.corpus, total))

    # ratio of this specific for loop in completion
    score = 1.0

    for step, doc in enumerate(docs):
      #print doc.name, doc.text()
      content = doc.text()
      # print doc.language
      #logger.debug('langauge %s %s' % (int(doc.id), doc.language.decode('utf-8')))
      if not doc.language or len(doc.language) == 0:
        language, probability = langid.classify(content[:255])
        doc.language = language
        doc.save()
      else:
        language = doc.language


      if doc.language == settings.FR:
        stopwords = FR_STOPWORDS
      elif doc.language == settings.NL:
        stopwords = NL_STOPWORDS
      else:
        stopwords = EN_STOPWORDS

      segments = distill(content, language=language, stopwords=stopwords)
      print segments

      with transaction.atomic():
        for i,(match, lemmata, tf, wf) in enumerate(segments):
          seg, created = Segment.objects.get_or_create(corpus=job.corpus, partofspeech=Segment.NP, content=match, defaults={
            'lemmata':  lemmata,
            'cluster':  lemmata,
            'language': language,
            'corpus' :  job.corpus
          })

          dos, created = Document_Segment.objects.get_or_create(document=doc, segment=seg)
          dos.tf=tf
          dos.wf=wf
          dos.save()
      job.document = doc
      job.completion = int(score*10000*step/total)/100.0
      job.save()
      logger.debug('tf executed language "%s" %s%%' % (language, job.completion))

    logger.debug('tf completed')

    


  def handle(self, *args, **options):
    if not options['cmd']:
      raise CommandError("\n    ouch. You should specify a valid function as cmd param")
    if not options['job_pk']:
      raise CommandError("\n    ouch. please provide a job id to record logs and other stuff")
    
    try:
      job = Job.objects.get(pk=options['job_pk'])
    except Job.DoesNotExist, e:
      logger.exception(e)
      raise CommandError("\n    ouch. Try again, job pk=%s does not exist!" % options['job_pk'])
    

    cmd = '_%s' % options['cmd']

    getattr(self, cmd)(job=job) # no job will be charged!
    
    job.completion = 1.0
    logger.debug('job completed')
    job.stop()

  
