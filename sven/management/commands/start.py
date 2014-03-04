import os, time
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from sven.models import Corpus, Document, Job


class Command(BaseCommand):
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
    self.stdout.write("\n------------------------------------------\n\n    welcome to sven script\n    ==================================\n\n\n\n")
    
    try:
      corpus = Corpus.objects.get(id=options['corpus'])
    except Corpus.DoesNotExist, e:
      raise CommandError("\n    ouch. Try again, corpus %s does not exist!" % options['corpus'])
    
    self.stdout.write(corpus.name)

    job = Job.start(corpus=corpus, command='harvest')

    # stop job
    self.stdout.write('job created with id:%s and status:%s' % (job.id, job.status)) 