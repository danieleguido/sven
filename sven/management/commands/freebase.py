import os, time, langid
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sven.distiller import distill, EN_STOPWORDS, FR_STOPWORDS, NL_STOPWORDS
from sven.models import Corpus, Job, Segment



class Command(BaseCommand):
  '''
  Beware! whooshing
  pip install Whoosh
  '''
  args = ''
  help = 'write a corpus document in an index'
  option_list = BaseCommand.option_list + (
      make_option('--corpus',
          action='store',
          dest='corpus',
          default=False,
          help='corpus id'),
  )


  @transaction.atomic
  def handle(self, *args, **options):
    # usage: python manage.py start --cmd=freebase --corpus=1
    # self.stdout.write("\n------------------------------------------\n\n    welcome to sven Whoosh indexer\n    ==================================\n\n\n\n")
    
    try:
      corpus = Corpus.objects.get(id=options['corpus'])
    except Corpus.DoesNotExist, e:
      raise CommandError("\n    ouch. Try again, corpus %s does not exist!" % options['corpus'])
    
    # self.stdout.write(corpus.name)

    try:
      job = Job.objects.get(corpus=corpus)
    except Job.DoesNotExist, e:
      raise CommandError("\n    ouch. Try again, corpus does not have any job connected....! Maybe you would like to do manage.py start --cmd=freebase --corpus=%s"% options['corpus'])

    segments = Segment.objects.filter(corpus=corpus)

    for s in segments:
      print s.content

    logger.debug('job completed')
    
    job.stop()

    exit()