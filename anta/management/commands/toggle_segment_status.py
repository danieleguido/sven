import os
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from anta.models import Corpus, Segment

class Command(BaseCommand):
  args = ''
  help = 'Clean every tags for the selected corpus'
  option_list = BaseCommand.option_list + (
      make_option('--corpus',
          action='store',
          dest='corpus',
          default=False,
          help='corpus name'),
      make_option('--exclude',
          action='store',
          dest='exclude',
          default=False,
          help='comma separated word to exclude from corpus'),
  )

  @transaction.commit_manually
  def handle(self, *args, **options):
    self.stdout.write("\n------------------------------------------\n\n    welcome to anta script\n    ==================================\n\n\n\n")
    
    #
    # 1. find corpus
    #
    try:
      corpus = Corpus.objects.get(name=options['corpus'])
    except Corpus.DoesNotExist, e:
      raise CommandError("\n    ouch. Try again, corpus %s does not exist!" % options['corpus'])
    
    self.stdout.write("\n    working on corpus %s:%s" % (corpus.id, corpus.name))
    
    # @todo put get path into model
    corpus_path = get_corpus_path(corpus)
    
    segs = Segment.objects.filter(status=Segment.STATUS_IN, document_segment__document__corpus=corpus)
    print segs.query
    
    stopregexp = options['exclude'].split(',') # e.g  ['study', 'change climate', 'person', 'world', 'book', 'global warming', 'student','film','year', 'states united', 'change', 'climate', 'editor', 'week', 'issue','state', 'country', 'text', 'photo', 'film series', 'filmmaker', 'front page']

    c = 0
    for seg in segs:
    	c = c+1
    	if seg.stemmed in stopregexp:
    		print c, seg.stemmed, Segment.STATUS_OUT
    		seg.status = Segment.STATUS_OUT
    		seg.save()
    		

    self.stdout.write("\n    documents free of strange texts!")
    
    self.stdout.write("\n\n-----------  finish  ---------------------\n\n")
    transaction.commit()
    

def get_corpus_path(corpus):
  return os.path.join(settings.MEDIA_ROOT, corpus.name)

def unicode_dict_reader(utf8_data, **kwargs):
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    for row in csv_reader:
        yield dict([(key, unicode(value, 'utf-8')) for key, value in row.iteritems()])