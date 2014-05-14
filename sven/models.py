#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re, os, signal, operator, mimetypes, shutil, urllib2, json, subprocess, logging, codecs
from datetime import datetime 

from django.conf import settings
from django.db import models, transaction, connection
from django.db.models import Q, Count
from django.db.models.signals import pre_delete, post_save
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.timezone import make_aware, utc
from django.dispatch import receiver

from sven.distiller import dry

logger = logging.getLogger("sven")




def helper_uuslug(model, instance, value, max_length=128):
  slug = slugify(value)[:max_length] # safe autolimiting
  slug_base = slug
  i = 1;

  while model.objects.exclude(pk=instance.pk).filter(slug=slug).count():
    candidate = '%s-%s' % (slug_base, i)
    if len(candidate) > max_length:
      slug = slug[:max_length-len('-%s' % i)]
    slug = re.sub('\-+','-',candidate)
    i += 1

  return slug



def helper_get_document_path(instance, filename):
  return os.path.join(instance.corpus.get_path(),filename)



def helper_user_to_dict(user):
  d = {
    'username': user.username
  }
  return d



def helper_palette():
  '''
  return a json dict containing a random generate palette.
  first result image, e.g http://www.colourlovers.com/paletteImg/94582D/B97820/F3B503/EA8407/957649/ThePeanuttyProfessor.png
    
    print helper_palette().pop()['imageUrl']
  
  '''
  request = urllib2.Request('http://www.colourlovers.com/api/palettes/random?format=json',
    headers={'User-Agent': "ColourLovers Browser"}
  )
  
  contents = urllib2.urlopen(request).read()
  return json.loads(contents)



def helper_colour():
  '''
  return a json dict containing a random generate color with a generated image.
  first result image, e.g http://www.colourlovers.com/paletteImg/94582D/B97820/F3B503/EA8407/957649/ThePeanuttyProfessor.png
    
    print helper_colour().pop()['hex']
    print helper_colour().pop()['imageUrl'] "hex":"A5CA68"
  
  '''
  request = urllib2.Request('http://www.colourlovers.com/api/colors/random?format=json',
    headers={'User-Agent': "ColourLovers Browser"}
  )
  
  contents = urllib2.urlopen(request).read()
  return json.loads(contents)  



class Profile(models.Model):
  user = models.OneToOneField(User)
  bio = models.TextField(null=True, blank=True)
  picture = models.URLField(max_length=160, blank=True, null=True)


  def json(self, deep=False):
    d = {
      'id': self.id,
      'bio_raw': self.bio,
      'bio': self.bio,
      'picture': self.picture,
      'username': self.user.username,
      'firstname': self.user.first_name,
      'lastname': self.user.last_name
    }
    return d


  def save(self, **kwargs):
    if self.pk is None or len(self.picture) == 0:
      try:
        self.picture = helper_palette()[0]['imageUrl']
      except urllib2.URLError, e:
        logger.error(e)
    super(Profile, self).save()



@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
  if created:
    pro = Profile(user=instance, bio="")
    pro.save()



class Corpus(models.Model):
  name = models.CharField(max_length=32)
  slug = models.CharField(max_length=32, unique=True)
  color = models.CharField(max_length=6, blank=True)

  date_created = models.DateTimeField(auto_now=True)
  date_last_modified = models.DateTimeField(auto_now_add=True)

  owners = models.ManyToManyField(User, related_name="corpora")


  def get_path(self):
    return os.path.join(settings.MEDIA_ROOT, self.slug)


  def save(self, **kwargs):
    self.slug = helper_uuslug(model=Corpus, instance=self, value=self.name)
    path = self.get_path()
    if not os.path.exists(path):
      os.makedirs(path)

    if self.pk is None or len(self.color) == 0:
      try:
        self.color = helper_colour()[0]['hex']
      except urllib2.URLError, e:
        logger.error(e)
    super(Corpus, self).save()


  def __unicode__(self):
    return '%s [%s]' % (self.name, self.slug)


  def json(self, deep=False):
    d = {
      'id': self.id,
      'name': self.name,
      'slug': self.slug,
      'color': '#%s' % self.color,
      'count':{
        'documents': self.documents.count(),
        'owners': self.owners.count()
      }
    }

    # raw query to ge count. Probably there should be a better place :D
    cursor = connection.cursor()
    cursor.execute('''
      SELECT COUNT(s.`cluster`)
      FROM sven_segment s
      WHERE corpus_id=%s
    ''', [self.id])
    d['count']['clusters'] = cursor.fetchone()[0]

    if deep:
      d.update({
        'owners': [helper_user_to_dict(u) for u in self.owners.all()]
      })
    return d


  class Meta:
    verbose_name_plural = 'corpora'



@receiver(post_save, sender=User)
def create_corpus(sender, instance, created, **kwargs):
  if created:
    cor = Corpus(name=u'%s-box' % instance.username)
    cor.save()
    cor.owners.add(instance)
    cor.save()



@receiver(pre_delete, sender=Corpus)
def delete_corpus(sender, instance, **kwargs):
  '''
  rename or delete the corpus path linked to the corpus instance.
  We should provide a zip with the whole text content under the name <user>.<YYYYmmdd>.<corpus-name>.zip, @todo
  '''
  path = instance.get_path()

  shutil.rmtree(path)



class Segment( models.Model): 
  OUT = 'OUT'
  IN = 'IN'

  STATUS_CHOICES = (
    (OUT, u'exclude'),
    (IN, u'include'),
  )

  NP = 'NP'
  POS_CHOICES = (
    (NP, u'noun phrase'),
  )

  content = models.CharField(max_length=128)
  lemmata = models.CharField(max_length=128)
  cluster = models.CharField(max_length=128) # index by cluster. Just to not duplicate info , e.g by storing them in a separate table. Later you can group them by cluster.

  corpus    = models.ForeignKey(Corpus, related_name="segments") # corpus specific [sic]
  language  = models.CharField(max_length=2, choices=settings.LANGUAGE_CHOICES)
  status    = models.CharField(max_length=3, choices=STATUS_CHOICES, default=IN)
  
  partofspeech = models.CharField(max_length=3, choices=POS_CHOICES)


  def __unicode__(self):
    return '%s [%s]' % (self.content, self.lemmata)


  def json(self, deep=False):
    d = {
      'id': self.id,
      'content': self.content,
      'cluster': self.cluster 
    }
    return d


  class Meta:
    unique_together = ('content', 'corpus', 'partofspeech')



class Freebase(models.Model):
  uid = models.CharField(max_length=64, unique=True)
  category = models.CharField(max_length=64)

  segments = models.ManyToManyField(Segment, null=True, blank=True)


  def json(self, deep=False):
    d = {
      'uid': self.uid, # uniqueid
      'category': self.category
    }
    return d



class Tag(models.Model):
  '''
  Clustering documents according to tag. A special tag category is actor.
  feel free to add tag type to this model ... :D
  '''
  FREE = '' # i.e, no special category at all
  ACTOR = 'ac'
  INSTITUTION = 'in'

  TYPE_CHOICES = (
    (FREE, 'no category'),
    (ACTOR, 'actor'),
    (INSTITUTION, 'Institution'),
  )

  name = models.CharField(max_length=128) # e.g. 'Mr. E. Smith'
  slug = models.SlugField(max_length=128, unique=True) # e.g. 'mr-e-smith'
  type = models.CharField(max_length=2, choices=TYPE_CHOICES, default=FREE) # e.g. 'actor' or 'institution'


  def save(self, **kwargs):
    if self.pk is None:
      self.slug = helper_uuslug(model=Tag, instance=self, value=self.name)
    super(Tag, self).save()


  @staticmethod
  def search(query):
    argument_list =[
      Q(name__icontains=query),
      Q(slug__icontains=query),   # add this only when there are non ascii chars in query. transform query into a sluggish field. @todo: prepare query as a slug
    ]
    return reduce(operator.or_, argument_list)

  def __unicode__(self):
    return "%s : %s"% (self.get_type_display(), self.name)


  def json(self, deep=False):
    d = {
      'id': self.id, # uniqueid
      'name': self.name,
      'slug': self.slug,
      'type': self.type
    }
    return d



class Document(models.Model):
  name = models.CharField(max_length=128)
  slug = models.CharField(max_length=128, unique=True)
  corpus = models.ForeignKey(Corpus, related_name='documents')
  
  language  = models.CharField(max_length=2, choices=settings.LANGUAGE_CHOICES)

  raw  = models.FileField(upload_to=helper_get_document_path, blank=True, null=True)
  mimetype = models.CharField(max_length=100)

  date = models.DateTimeField(blank=True, null=True)
  date_created = models.DateTimeField(auto_now=True)
  date_last_modified = models.DateTimeField(auto_now_add=True)

  url = models.URLField(blank=True, null=True) # external url to be boilerplated

  segments = models.ManyToManyField(Segment, through="Document_Segment", blank=True, null=True)
  tags = models.ManyToManyField(Tag, blank=True, null=True)


  def json(self, deep=False):
    d = {
      'id': self.id,
      'name': self.name,
      'slug': self.slug,
      'mimetype': self.mimetype,
      'language': self.language,
      'date': self.date.strftime("%Y-%m-%d") if self.date else None,
      'date_created': self.date_created.isoformat(),
      'date_last_modified': self.date_last_modified.isoformat(),
      'tags': [t.json() for t in self.tags.all()]
    }

    if self.mimetype != "text/plain":
      d['media'] = os.path.join(settings.MEDIA_URL, self.corpus.slug, os.path.basename(self.raw.url))
      
    if deep:
      d.update({
        'text': self.text(),
        'corpus': self.corpus.json()
      })
    return d


  def __unicode__(self):
    return '%s [%s]' % (self.name, self.slug)


  @staticmethod
  def get_whoosh():
    '''
    return inbdex instance currently installed or (tyies) to install it.
    todo check posssible errors!!!!!!!
    And what about declaring import here ?
    '''
    from whoosh.index import create_in, exists_in, open_dir
    from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
    
    schema = Schema(title=TEXT(stored=True), path=ID(unique=True, stored=True), content=TEXT(stored=True), tags=KEYWORD)
    
    if not os.path.exists(settings.WHOOSH_PATH):
      os.mkdir(settings.WHOOSH_PATH)
    
    if not exists_in(settings.WHOOSH_PATH):
      index = create_in(settings.WHOOSH_PATH, schema)
    else:
      index = open_dir(settings.WHOOSH_PATH)
    return index


  @staticmethod
  def indexed_search(query, epoxy):
    '''
    test: http://localhost:8000/api/corpus/1/document?search=king&indent
    '''
    from whoosh.qparser import QueryParser

    ix = Document.get_whoosh()
    parser = QueryParser("content", ix.schema)
    q = parser.parse(query)

    with ix.searcher() as searcher:
    #results = s.search(q)
      results = searcher.search(q, limit=200)
      epoxy.meta('total_count',  len(results))
      epoxy.meta('query', query)
      objs = []
      ids = []
      items=[]
      for hit in results[epoxy.offset: epoxy.offset+epoxy.limit]:
        ids.append(hit['path'])
        items.append(hit)

      qs = Document.objects.filter(id__in=ids)
      for d in qs:
        doc = d.json()
        doc['match'] = items[ids.index(u"%s"%d.id)].highlights("content")
        objs.append(doc)

      epoxy.add('objects',objs)


  def text(self):
    '''
    Get utf8 text content of the file
    '''
    if self.mimetype == 'text/plain':
      with codecs.open(self.raw.path, encoding='utf-8', mode='r') as f:
        content = f.read()
    else:
      textified = '%s.txt' % self.raw.path
      if os.path.exists(textified):
        with codecs.open(textified, encoding='utf-8', mode='r') as f:
          content = f.read()
        
      else:
        content = '%s does not have a text associed. %s' % (self.mimetype, textified)
      # exitsts text translations?
      
    
    # clean content
    content = dry(content)

    return content


  def save(self, **kwargs):
    # understanding datetime included in file title... YYYY MM DD
    date = re.search(r'(?P<year>\d{4})[\-\./]*(?P<month>\d{2})[\-\./]*(?P<day>\d{2})',self.name)
    if date:
      self.date = make_aware(datetime.strptime('%s-%s-%s' % (date.group('year'), date.group('month'), date.group('day')), '%Y-%m-%d'), utc)

    self.slug = helper_uuslug(model=Document, instance=self, value=self.name)
    if self.raw:
      self.mimetype = mimetypes.guess_type(self.raw.path)[0]

    super(Document, self).save()
  


class Job(models.Model):
  STARTED = 'BOO'
  RUNNING = 'RUN'
  LOST = 'RIP'
  COMPLETED = 'END'

  STATUS_CHOICES = (
    (STARTED, u'started'),
    (RUNNING, u'running'),
    (LOST, u'process not found'),
    (COMPLETED, u'job completed')  
  )

  pid = models.CharField(max_length=32)
  cmd = models.TextField()
  corpus = models.ForeignKey(Corpus, unique=True)
  document = models.ForeignKey(Document, null=True, blank=True) # current working on document...

  status = models.CharField(max_length=3, choices=STATUS_CHOICES, default=STARTED)
  completion = models.FloatField(default='0')

  date_created = models.DateTimeField(auto_now=True)
  date_last_modified = models.DateTimeField(auto_now_add=True)


  def __unicode__(self):
    return '%s [pid=%s]' % (self.corpus.name, self.pid)


  def is_alive(self):
    logger.debug('Checking if a job is already running... ')
    
    try:
      s = subprocess.check_output('ps aux | grep "%s"' % self.cmd, shell=True, close_fds=True).split('\n')
      logger.debug(s)
    except OSError, e:
      logger.exception(e)
      return True
    #print s
    for g in s:
      if re.search(r'\d\s%s' % self.cmd, g) is None:
        logger.debug('no job running with pid=%s' % self.pid)
        return False
    logger.debug('job running... take it easy')
    return True


  @staticmethod
  def is_busy():
    running_jobs = Job.objects.filter(status__in=[Job.RUNNING, Job.STARTED])
    logger.debug('Job.is_busy() : checking already working jobs')
      
    if running_jobs.count() > 0:
      for r in running_jobs:
        if r.is_alive():
          logger.debug('A job is currently running!')
          return True
        else:
          r.status = Job.LOST
          r.save()
      # if reached the end of the loop, all running job found are lost... so Job can do something again!
      logger.debug('closing all previous job, since no one is alive.')
      return False
    else:
      logger.debug('no jobs running...')
      return False


  @staticmethod
  def start(corpus, command='harvest', popen=True):
    '''
    Check if there are jobs running, otherwise
    Ouptut None or the created job.
    Test with:
    http://localhost:8000/api/corpus/1/start/harvest
    http://localhost:8000/api/corpus/1/start/whoosher
    '''
    # check if there are job running...
    if Job.is_busy():
      logger.debug('job is busy %s' % command) 
      
      return None
    if command not in settings.STANDALONE_COMMANDS:
      logger.debug('command "%s" not stored as management command, running start command instead' % command) 
      # cpmmand stored into start
      popen_args = [settings.PYTHON_INTERPRETER, os.path.join(settings.BASE_DIR,'manage.py'), 'start', '--cmd', command, '--corpus']
    else:
      logger.debug('command "%s" popopened' % command) 
      popen_args = [settings.PYTHON_INTERPRETER, os.path.join(settings.BASE_DIR,'manage.py'), command, '--corpus']
    logger.debug('starting cmd "%s"%s' % (command, ' as subprocess' if popen else '' ))
    job, created = Job.objects.get_or_create(corpus=corpus)
    job.status = Job.RUNNING
    job.cmd = ' '.join(popen_args[:-1])
    job.save()

    popen_args.append(str(corpus.id))
    if popen:
      s = subprocess.Popen(popen_args, stdout=None, stderr=None, close_fds=True)
      job.pid = s.pid
    else:
      job.pid = 0

    return job


  def stop(self):
    self.status=Job.COMPLETED
    self.save()
    if self.pid != 0:
      logger.debug('killing pid %s' % int(self.pid))
      try:
        os.kill(int(self.pid), signal.SIGKILL)
      except OSError, e:
        logger.exception(e)
    # everything below will not be executed, since the process id has benn killed.



class Document_Segment( models.Model ):
  document = models.ForeignKey(Document, related_name="document_segments")
  segment = models.ForeignKey(Segment, related_name="document_segments")

  tf = models.FloatField(default=0) # term normalized frequency of the stemmed version of the segment
  tfidf = models.FloatField( default=0) # inversed term calculated according to the document via the stemmed version
  wf = models.FloatField(default=0) # sublinear tf scaling (normalized on logarithm) = log(tf) if tf > 0
  tfidf = models.FloatField( default=0) # inversed term calculated according to the document via the stemmed version


  def json(self, deep=False):
    d = self.segment.json()
    d.update({
      'tf': self.tf,
      'wf': self.wf,
      'num_clusters': self.num_clusters
    })
    return d


  class Meta:
    unique_together = ("segment", "document")



class Distance( models.Model ):
  alpha = models.ForeignKey(Document, related_name="alpha")
  omega = models.ForeignKey(Document, related_name="omega")
  cosine_similarity = models.FloatField( default='0')
  

  class Meta:
    unique_together = ("alpha", "omega")



class Sentence( models.Model ):
  '''
  May contain something e.g to store a match result. Not used,
  DEPRECATED
  '''
  content = models.TextField()
  position = models.IntegerField()
  document =  models.ForeignKey(Document)

