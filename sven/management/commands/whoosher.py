#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, time, langid, logging, re
from optparse import make_option
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from sven.models import Corpus, Job, Segment, Document




logger = logging.getLogger("sven")


class Command(BaseCommand):
  '''
  Beware! whooshing
  pip install Whoosh
  '''
  args = ''
  help = 'write a corpus document in an index. usage: $ python manage.py start --cmd=whoosh --corpus=1'
  option_list = BaseCommand.option_list + (
      make_option('--corpus',
          action='store',
          dest='corpus',
          default=False,
          help='corpus id'),
  )


  def handle(self, *args, **options):
    # 
    self.stdout.write("\n------------------------------------------\n\n    welcome to sven Whoosh indexer\n    ==================================\n\n\n\n")
    
    try:
      corpus = Corpus.objects.get(id=options['corpus'])
      job = Job.objects.get(corpus=corpus)
    except Corpus.DoesNotExist, e:
      raise CommandError("\n    ouch. Try again, corpus %s does not exist!" % options['corpus'])
    except Job.DoesNotExist, e:
      raise CommandError("\n    ouch. Try again, corpus does not have any job connected....! Maybe you would like to do manage.py start --cmd=freebase --corpus=%s"% options['corpus'])

    # staring index if needed    
    ix = Document.get_whoosh()
    logger.debug('index started')
    # creating writer
    writer = ix.writer() # multi thread cfr. from whoosh.writing import AsyncWriter

    for doc in corpus.documents.all():
      writer.add_document(
        title=doc.name,
        path = u"%s"%doc.id,
        content=doc.text())
    
    writer.commit()
    
    logger.debug('index compiled successfully')

    #from whoosh.qparser import QueryParser
    #parser = QueryParser("content", ix.schema)
    #q = parser.parse("summer")

    
    #qp = qparser.QueryParser("path", schema=ix.schema) q = qp.parse(u"test_id:alfa")
    #with ix.searcher() as searcher:
      #results = s.search(q)
    #  results = searcher.search(q)
    #  print len(results), results[0], results[0].highlights("content")


    logger.debug('job completed')
    
    job.stop()