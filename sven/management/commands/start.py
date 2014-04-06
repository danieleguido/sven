import os, time, logging
from optparse import make_option

from django.conf import settings
from django.db import transaction
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand, CommandError
from sven.models import Corpus, Document, Job, Document_Segment, Segment

logger = logging.getLogger("sven")

class Command(BaseCommand):
  args = ''
  help = 'execute a pos text extraction on a corpus'
  option_list = BaseCommand.option_list + (
      make_option('--corpus',
          action='store',
          dest='corpus',
          default=False,
          help='corpus id'),
      make_option('--cmd',
          action='store',
          dest='cmd',
          default=False,
          help='manage.py command to be executed'),
  )

  def handle(self, *args, **options):
    # self.stdout.write("\n------------------------------------------\n\n    welcome to sven script\n    ==================================\n\n\n\n")
    if not options['cmd']:
       raise CommandError("\n    ouch. You should specify a valid function as cmd param")
    logger.debug('-------------------------------------------')
    logger.debug('handling cmd "%s"' % options['cmd'])

    try:
      corpus = Corpus.objects.get(id=options['corpus'])
    except Corpus.DoesNotExist, e:
      raise CommandError("\n    ouch. Try again, corpus %s does not exist!" % options['corpus'])
    
    popen = True
    if options['cmd'] in ['whoosh', 'harvest']:
      job = Job.start(corpus=corpus, command=options['cmd'], popen=popen)
    else:
      try:
        getattr(self, 'misc_%s' % options['cmd'])(corpus=corpus, options=options) # no job will be charged!
      except AttributeError, e:
        logger.exception(e)
        raise CommandError("\n    ouch. Try again, command %s does not exist!" % options['cmd'])
      except CommandError, e:
        raise
      except Exception, e:
        logger.exception(e)
        raise
        

    
    # stop job
    # self.stdout.write('job created with id:%s and status:%s' % (job.id, job.status))

  @transaction.atomic
  def misc_reset(self, corpus, options):
    logger.debug('executing "%s"...' % options['cmd'])
    job = Job.start(corpus=corpus, command=options['cmd'], popen=False)
    if job is None:
      raise CommandError("\n    Try again later, server is busy and some process is yet running...")
    
    Document_Segment.objects.filter(document__corpus=corpus).delete()
    logger.debug('completed "%s" on corpus %s' % (options['cmd'], corpus))
    job.stop()
    

  @transaction.atomic
  def misc_segmentreset(self, corpus, options):
    logger.debug('executing "%s"...' % options['cmd'])
    job = Job.start(corpus=corpus, command=options['cmd'], popen=False)
    if job is None:
      raise CommandError("\n    Try again later, server is busy and some process is yet running...")
    
    segments = Segment.objects.all()
    for s in segments:
      s.delete()

    logger.debug('completed "%s" on corpus %s' % (options['cmd'], corpus))
    job.stop()
