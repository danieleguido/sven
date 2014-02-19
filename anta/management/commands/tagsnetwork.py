import os, csv, codecs
import networkx as nx
from networkx.algorithms import bipartite
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.core.files import File
from anta.models import Corpus, Tag, Document, Document_Tag, Segment


class Command(BaseCommand):
  args = ''
  help = 'Get the tag networks'
  option_list = BaseCommand.option_list + (
      make_option('--corpus',
          action='store',
          dest='corpus',
          default=False,
          help='corpus name'),
      make_option('--output',
          action='store',
          dest='output',
          default='tagsnetworks.gexf',
          help='gexf output'),
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
    query = Tag.objects.raw( 
      """
      SELECT t.id, t.name, d.id as document_id, d.title as document_title
        FROM anta_document_tag dt
        JOIN anta_tag t ON t.id = dt.tag_id
        JOIN anta_document d ON d.id = dt.document_id
      WHERE d.corpus_id = %s
      AND t.type != 'actor'
      ORDER BY t.id
      """,[corpus.id]
    )

    G=nx.Graph()
    top_nodes = []

    for t in query:
      G.add_nodes_from(['t%s' % t.id], label=t.name)
      G.add_nodes_from(['d%s' % t.document_id], label=t.document_title)
      G.add_edge('t%s' % t.id, 't%s' % t.document_id)
        # computate edges for t.id

    # G1 = bipartite.weighted_projected_graph(G,top_nodes)

    nx.write_gexf(G, options['output'])
    

    

    self.stdout.write("\n\n-----------  finish  ---------------------\n\n")


def get_corpus_path(corpus):
  return os.path.join(settings.MEDIA_ROOT, corpus.name)

def unicode_dict_reader(utf8_data, **kwargs):
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    for row in csv_reader:
        yield dict([(key, unicode(value, 'utf-8')) for key, value in row.iteritems()])