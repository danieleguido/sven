#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, time, langid, logging
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sven.distiller import distill, EN_STOPWORDS, FR_STOPWORDS, NL_STOPWORDS
from sven.models import Corpus, Document, Job, Segment, Document_Segment



logger = logging.getLogger("sven")



class Command(BaseCommand):
  '''
  Install langid from pip:
  pip install https://pypi.python.org/packages/source/l/langid/langid-1.1.4dev.tar.gz
  '''
  args = ''
  help = 'execute a pos text extraction on a corpus'
  option_list = BaseCommand.option_list + (
      make_option('--corpus',
          action='store',
          dest='corpus',
          default=False,
          help='corpus id'),
  )


  def handle(self, *args, **options):
    # self.stdout.write("\n------------------------------------------\n\n    welcome to sven script\n    ==================================\n\n\n\n")
    logger.debug('executing "harvest"...')
    try:
      corpus = Corpus.objects.get(id=options['corpus'])
    except Corpus.DoesNotExist, e:
      logger.exception(e)
      raise CommandError("\n    ouch. Try again, corpus %s does not exist!" % options['corpus'])
    
    # self.stdout.write(corpus.name)

    
    try:
      job = Job.objects.get(corpus=corpus)
    except Job.DoesNotExist, e:
      logger.exception(e)
      raise CommandError("\n    JOB having this corpus does not exist. IS THAT POSSIBLE? does not have any job connected....!")

    docs = corpus.documents.all()
    total = docs.count()

    logger.debug('corpus %s contains %s documents' % (corpus, total))

    logger.debug('corpus%s' % options['corpus'] )
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
          seg, created = Segment.objects.get_or_create(corpus=corpus, partofspeech=Segment.NP, content=match, defaults={
            'lemmata':  lemmata,
            'cluster':  lemmata,
            'language': language,
            'corpus' :  corpus
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

    job.completion = 1.0
    job.stop()
    logger.debug('job completed')
    # let's calculate tfidf
    exit()