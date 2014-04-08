import os, time, langid, logging, re
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sven.distiller import distill, EN_STOPWORDS, FR_STOPWORDS, NL_STOPWORDS, freebase
from sven.models import Corpus, Job, Segment



logger = logging.getLogger("sven")


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


  def handle(self, *args, **options):
    # usage: python manage.py start --cmd=freebase --corpus=1
    # self.stdout.write("\n------------------------------------------\n\n    welcome to sven Whoosh indexer\n    ==================================\n\n\n\n")
    
    try:
      corpus = Corpus.objects.get(id=options['corpus'])
      job = Job.objects.get(corpus=corpus)
    except Corpus.DoesNotExist, e:
      raise CommandError("\n    ouch. Try again, corpus %s does not exist!" % options['corpus'])
    except Job.DoesNotExist, e:
      raise CommandError("\n    ouch. Try again, corpus does not have any job connected....! Maybe you would like to do manage.py start --cmd=freebase --corpus=%s"% options['corpus'])

    if_is_acronym = re.compile(r'[A-Z][A-Z]{2,}')
    if_contains_uppercase = re.compile(r'[A-Z][a-z]{2,}')
   
    with transaction.atomic():
      segments = Segment.objects.filter(corpus=corpus)

      for s in segments:
        is_acronym = if_is_acronym.search(s.content) 
        if is_acronym is not None:
          print "ACRO", is_acronym.group(), s.language

          concepts = freebase(query=s.content, lang=s.language, api_key=settings.FREEBASE_KEY)
          for c in concepts:
            print c

        else:
          contains_uppercase = if_contains_uppercase.search(s.content) 
          if contains_uppercase is not None:
            print(contains_uppercase.group())

    logger.debug('job completed')
    
    job.stop()

    exit()