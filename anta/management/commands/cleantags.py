import os, csv, codecs
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.core.files import File
from anta.models import Corpus, Tag, Document, Document_Tag


class Command(BaseCommand):
  args = ''
  help = 'Clean every tags for the selected corpus'
  option_list = BaseCommand.option_list + (
      make_option('--corpus',
          action='store',
          dest='corpus',
          default=False,
          help='corpus name'),
  )

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
    
    ds = Document_Tag.objects.filter(document__corpus=corpus)
    ds.delete()
    self.stdout.write("\n    documents free of tags!")
    
    self.stdout.write("\n\n-----------  finish  ---------------------\n\n")


def get_corpus_path(corpus):
  return os.path.join(settings.MEDIA_ROOT, corpus.name)

def unicode_dict_reader(utf8_data, **kwargs):
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    for row in csv_reader:
        yield dict([(key, unicode(value, 'utf-8')) for key, value in row.iteritems()])