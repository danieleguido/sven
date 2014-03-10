import os, time, langid
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sven.distiller import distill, EN_STOPWORDS, FR_STOPWORDS, NL_STOPWORDS
from sven.models import Corpus, Document, Job, Segment, Document_Segment



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

  @transaction.atomic
  def handle(self, *args, **options):
    self.stdout.write("\n------------------------------------------\n\n    welcome to sven script\n    ==================================\n\n\n\n")
    
    try:
      corpus = Corpus.objects.get(id=options['corpus'])
    except Corpus.DoesNotExist, e:
      raise CommandError("\n    ouch. Try again, corpus %s does not exist!" % options['corpus'])
    
    self.stdout.write(corpus.name)

    try:
      job = Job.objects.get(corpus=corpus)
    except Job.DoesNotExist, e:
      raise CommandError("\n    ouch. Try again, corpus does not have any job connected....!")

    for doc in corpus.documents.all():
      job.document = doc
      job.save()
      #print doc.name, doc.text()
      content = doc.text()

      if not doc.language:
        language, probability = langid.classify(content[:255])
        doc.language = language
        doc.save()

      if doc.language == settings.FR:
        stopwords = FR_STOPWORDS
      elif doc.language == settings.NL:
        stopwords = NL_STOPWORDS
      else:
        stopwords = EN_STOPWORDS

      segments = distill(content, language=language, stopwords=stopwords)
      
      for i,(match, lemmata, tf, wf) in enumerate(segments):
        seg, created = Segment.objects.get_or_create(content=match, lemmata=lemmata, cluster=lemmata, language=language)
        dos, created = Document_Segment.objects.get_or_create(document=doc, segment=seg, tf=tf, wf=wf)

    job.completion = .25
    job.save()


    # let's calculate tfidf


    


