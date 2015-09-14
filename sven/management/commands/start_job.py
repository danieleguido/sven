#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, unicodecsv, time, codecs, shutil, urllib2, logging, langid
from optparse import make_option
from datetime import datetime

from django.conf import settings
from django.db import transaction, connection
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from sven.models import Corpus, Document, Tag, Job, Document_Segment, Segment
from sven.forms import DocumentMetadataForm


logger = logging.getLogger("sven")



class Command(BaseCommand):
  '''
  usage type:
  
  python manage.py start_job --job=1 --cmd=test
  '''
  args = ''
  help = 'execute some job on corpus.'
  option_list = BaseCommand.option_list + (
    make_option('--job',
      action='store',
      dest='job_pk',
      default=False,
      help='job primary key related with a corpus'),

    make_option('--cmd',
        action='store',
        dest='cmd',
        default=False,
        help='manage.py command to be executed'),

    make_option('--csv',
        action='store',
        dest='csv',
        default=False,
        help='csv file (used only in import tags or concepts)'),
  )


  def _test(self, job, options):
    job.completion = 0
    while job.completion < 1:
      job.completion = min(1.0, job.completion + 0.1)
      job.save()
      time.sleep(10)
  


  def _alchemy(self, job, options):
    '''
    Enrich document with alchemy top entities (max: 5)
    '''
    number_of_documents = job.corpus.documents.count()
    
    docs = job.corpus.documents.all()
    c = 0.0
    for doc in docs:
      c += 1
      with transaction.atomic():
        try:
          doc.autotag()
        except Exception,e:
          logger.exception(e)
        job.completion = c/number_of_documents
        job.save()


  def _cleansegments(self, job, options):
    '''
    Remove only analisys result leaving document untouched.
    Useful when adding a stopword list and start over the extraction process.
    '''
    logger.debug('executing "clean segments" corpus...')
    number_of_documents = job.corpus.documents.count()
    
    docs = job.corpus.documents.all()

    for step, doc in enumerate(docs):
      with transaction.atomic():
        Document_Segment.objects.filter(document=doc).delete()
      job.completion = 1.0*step/number_of_documents
      job.save()
    logger.debug('executing "clean segments" finished')



  def _clean(self, job, options):
    logger.debug('executing "clean" corpus...')
    number_of_documents = job.corpus.documents.count()
    
    docs = job.corpus.documents.all()

    for step, doc in enumerate(docs):
      with transaction.atomic():
        Job.objects.filter(document=doc).update(document=None)
        Document_Segment.objects.filter(document=doc).delete()
        doc.delete()
      job.completion = 1.0*step/number_of_documents
      job.save()
    logger.debug('executing "clean" finished')



  def _removecorpus(self, job, options):
    logger.debug('removing corpus - would remove job also...')
    job.corpus.delete()



  def _tfidf(self, job, options):
    import math
    from django.db.models import F
    from sven.distiller import dictfetchall

    number_of_documents = job.corpus.documents.count()
    number_of_segments  = job.corpus.segments.count()

    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(distinct cluster) FROM sven_segment s WHERE s.corpus_id = %(corpus)s" %{
      'corpus': job.corpus.id
    })
    row = cursor.fetchone()
    number_of_clusters = row[0] # clusters in corpus

    
    if number_of_documents == 0:
      raise Exception('not enough "documents" in corpus to perform tfidf')# @todo

    if number_of_segments == 0:
      raise Exception('not enough "segments" in corpus to perform tfidf')# @todo

    # 2. get all languages in corpus
    number_of_languages = job.corpus.segments.values('language').distinct()
    
    logger.info("number_of_documents %s" % number_of_documents)
    logger.info("number_of_segments %s" % number_of_segments)
    logger.info("number_of_languages %s" % number_of_languages)
    # 3. start querying per language stats
    cursor = connection.cursor()

    step = 0;
    for i in number_of_languages:
      language = i['language']
      # get number of clusters per language to print completion percentage (can we save it if self.job exists)
      #clusters = self.segments.filter(language=language).values('cluster').annotate(Count('cluster'))
      #for c in clusters:
      #  print c['cluster'], c

      # distribution query. In how many document can a cluster be found?
      clusters = cursor.execute("""
        SELECT
          COUNT( DISTINCT ds.document_id ) as distribution, 
          s.language,
          s.cluster
        FROM `sven_document_segment` ds
        JOIN `sven_segment` s ON ds.segment_id = s.id
        JOIN `sven_document` d ON d.id = ds.document_id
        WHERE d.corpus_id = %s AND s.language = %s AND s.status = %s
        GROUP BY s.cluster
        ORDER BY distribution DESC, cluster ASC""", [
          job.corpus.id,
          language,
          Segment.IN
        ]
      )
      
      for i, cluster in enumerate(dictfetchall(cursor)):
        step = step+1
        
        with transaction.atomic():  
          # for each cluster, calculate df value inside the overall corpus.
          df = float(cluster['distribution'])/number_of_documents
          ## UPDATE sven_document_segment SET tfidf = tf*2 WHERE document_id = 218 
          #
          Document_Segment.objects.filter(
            segment__cluster=cluster['cluster'],
            segment__language=language
          ).update(tfidf=F('tf') * math.log(1/df))
          # .update
          # group by cluster and update value for the document_segment table. TFIDF is specific for each couple.
          #for ds in Document_Segment.objects.filter(segment__cluster=cluster['cluster'], segment__language=language):
          #  ds.tfidf = ds.tf * math.log(1/df) 
          #  ds.wfidf = ds.wf * math.log(1/df)
          #  #print i, cluster['cluster'], df, ds.tf, ds.tfidf
          #  ds.save()

          job.completion = 1.0*step/number_of_clusters
          job.save()

        if job.completion*100 % 4 == 0:  # every 2.5%
          logger.info("completion %s" % job.completion)
      logger.info("terminating (loop completed)...")


  def _importconcepts(self, job, options):
    if not options['csv'] or not os.path.exists(options['csv']):
      logger.debug('%s does not exist', options['csv'])
      return
    logger.debug('executing "import concepts" on csv %s' % options['csv'])
    total = sum(1 for line in open(options['csv']))
    # stqrt importing here
    f = open(options['csv'], 'rb')
    rows = unicodecsv.DictReader(f, encoding='utf-8')
    #rows = unicodecsv.DictReader(f)
    # get number of rows
    logger.debug('%s lines in csv file, starting import' % total)
    
    with transaction.atomic():

      for step,row in enumerate(rows):
        logger.debug('import line %s of %s' % (step, total))
        Segment.objects.filter(corpus=job.corpus, cluster=row[u'segment__cluster']).update(cluster=row[u'cluster'].strip(), status=(Segment.OUT if len(row[u'cluster'].strip()) == 0 else Segment.IN))
        
    self._tfidf(job, options)

  def _importtags(self, job, options):
    '''
    Import given tags for the given corpus from a csv file.
    The csv file must have a 'key' field. Note that any changes is undouable. 
    (todo) Anyway, a copy of the previous csv should be available to restore the system at a previous state.
    '''
    logger.debug('executing "import tags"...')

    if not options['csv'] or not os.path.exists(options['csv']):
      logger.debug('%s does not exist', options['csv'])
      return

    total = sum(1 for line in open(options['csv']))

    f = open(options['csv'], 'rb')
    rows = unicodecsv.DictReader(f, encoding='utf-8')
    #rows = unicodecsv.DictReader(f)
    # get number of rows
    logger.debug('%s lines in csv file, starting import' % total)
      
    for step,row in enumerate(rows):
      logger.debug('import line %s of %s' % (step, total))
      name = row['name'] # change document title (it has to be a complete csv export !!!!)
      language = row['language'][:2]

      job.completion = 1.0*step/total
      

      form = DocumentMetadataForm(row)
      if row['date'] and not form.is_valid():
        logger.error('validating csv fields... %s' % row['date'])
        logger.error(form.errors)
        job.save()
        continue

      date = form.cleaned_data['date'] if row['date'] else None

      try:
        doc = Document.objects.get(pk=row['key'], corpus=job.corpus)
      except Document.DoesNotExist, e:
        logger.debug('document %(id)s does not exists, or it does not belong to corpus %(corpus)s',{
          'id': row['key'],
          'corpus': job.corpus.name
        })
        job.save()
        continue # skip and check next document

      job.document = doc
      job.save()

      with transaction.atomic():
        doc.name     = name
        doc.language = language
        doc.date     = date

        doc.tags.clear() # delete previous tags. filter.
        
        for tag_type,tag_label in Tag.TYPE_CHOICES: # restrict possible values
          tags = filter(None, row[tag_label].split(','))
          # create tag if needed
          # remove old tag
          logger.debug('import tags %s - %s at line %s of %s' % (tags, tag_label, step, total))
      
          for t in tags:
            tag, created = Tag.objects.get_or_create(name=t,type=tag_type)
            doc.tags.add(tag)
        
        doc.save()

      


  def _harvest(self, job, options):
    from sven.distiller import distill, EN_STOPWORDS, FR_STOPWORDS, NL_STOPWORDS, IT_STOPWORDS

    logger.debug('executing "harvest"...')
    
    docs = job.corpus.documents.all()
    total = docs.count()

    logger.debug('corpus %s: contains %s documents' % (job.corpus, total))

    # ratio of this specific for loop in completion
    score = 1.0

    # clean segments
    Segment.objects.filter(corpus=job.corpus).delete()
    logger.debug('corpus %(corpus)s: deleting segments', {
        'corpus': job.corpus
    })

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
      elif doc.language == settings.IT:
        stopwords = IT_STOPWORDS
      else:
        stopwords = EN_STOPWORDS

      segments = distill(content, language=language, stopwords=stopwords)
      #print segments
      

      with transaction.atomic():
        
        
        

        for i,(match, lemmata, tf, wf) in enumerate(segments):
          seg, created = Segment.objects.get_or_create(corpus=job.corpus, partofspeech=Segment.NP, content=match[:128], defaults={
            'lemmata':  lemmata[:128],
            'cluster':  lemmata[:128],
            'language': language,
            'corpus' :  job.corpus
          })

          dos, created = Document_Segment.objects.get_or_create(document=doc, segment=seg)
          dos.tf=tf
          dos.wf=wf
          dos.save()
          

      
        job.document = doc
        job.completion = 1.0*step/total
        job.save()
      logger.debug('tf doc id:%(id)s, language:%(language)s, completion %(step)s / %(total)s' % {
        'id': doc.id,
        'language': language,
        'step': step,
        'total': total
      })

    logger.debug('tf completed')

  

  def _whoosher(self, job, options): 
    self.stdout.write("\n------------------------------------------\n\n    welcome to sven Whoosh indexer\n    ==================================\n\n\n\n")

    # staring index if needed    
    ix = Document.get_whoosh()
    logger.debug('index started')
    # creating writer
    writer = ix.writer() # multi thread cfr. from whoosh.writing import AsyncWriter

    total = job.corpus.documents.count()
    
    for step, doc in enumerate(job.corpus.documents.all()):
      writer.delete_by_term('path', u'%s' % doc.id)
      writer.add_document(
        title=doc.name,
        path = u'%s' % doc.id,
        content=doc.text()
      )

      job.document = doc
      job.completion = 1.0 * step/total
      job.save()

    writer.commit()
    
    logger.debug('index compiled successfully')



  def handle(self, *args, **options):
    if not options['cmd']:
      raise CommandError("\n    ouch. You should specify a valid function as cmd param")
    if not options['job_pk']:
      raise CommandError("\n    ouch. please provide a job id to record logs and other stuff")
    
    try:
      job = Job.objects.get(pk=options['job_pk'])
    except Job.DoesNotExist, e:
      logger.exception(e)
      raise CommandError("\n    ouch. Try again, job pk=%s does not exist!" % options['job_pk'])
    
    try:
      cmd = '_%s' % options['cmd']

      getattr(self, cmd)(job=job, options=options) # no job will be charged!
    except Exception, e:
      logger.exception(e)
    else:
      job.completion = 1.0
      logger.debug('job %s completed' %options['cmd'])
    
    job.stop()


  
