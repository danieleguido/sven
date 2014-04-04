#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re, os, signal, mimetypes, shutil, urllib2, json, subprocess, logging
from datetime import datetime 

from django.conf import settings
from django.db import models, transaction
from django.db.models import Count
from django.db.models.signals import pre_delete, post_save
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.timezone import make_aware, utc
from django.dispatch import receiver



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
  bio = models.TextField()
  picture = models.URLField(max_length=160, blank=True, null=True)


  def json(self, deep=False):
    d = {
      'id': self.id,
      'bio_raw': self.bio,
      'picture': self.picture,
      'username': self.user.username
    }
    return d

  def save(self, **kwargs):
    if self.pk is None or len(self.picture) == 0:
      self.picture = helper_palette()[0]['imageUrl']
    
    super(Profile, self).save()



@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
  if created:
    pro = Profile(user=instance, bio="")
    pro.save()



class Corpus(models.Model):
  name = models.CharField(max_length=32)
  slug = models.CharField(max_length=32, unique=True)
  color = models.CharField(max_length=6, blank=True, null=True)

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
      self.color = helper_colour()[0]['hex']
    
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
    if deep:
      d.update({
        'owners': [helper_user_to_dict(u) for u in self.owners.all()]
      })
    return d


  class Meta:
    verbose_name_plural = 'corpora'



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

  language  = models.CharField(max_length=2, choices=settings.LANGUAGE_CHOICES)
  status    = models.CharField(max_length=3, choices=STATUS_CHOICES, default=IN)
  
  partofspeech = models.CharField(max_length=3, choices=POS_CHOICES)
  

  def __unicode__(self):
    return '%s [%s]' % (self.content, self.lemmata)


  def json(self, deep=False):
    d = {
      'content': self.content,
      'cluster': self.cluster,
      'max_tf': self.max_tf if 'max_tf' in self else 0.0
    }
    return d


  class Meta:
    unique_together = ('content', 'language', 'partofspeech')



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


  def json(self, deep=False):
    d = {
      'id': self.id,
      'name': self.name,
      'slug': self.slug,
      'mimetype': self.mimetype,
      'language': self.language,
      'date': self.date.strftime("%Y-%m-%d"),
      'date_created': self.date_created.isoformat(),
      'date_last_modified': self.date_last_modified.isoformat()
    }
    if deep:
      d.update({
        'text': self.text(),
        'corpus': self.corpus.json()
      })
    return d


  def __unicode__(self):
    return '%s [%s]' % (self.name, self.slug)


  def text(self):
    '''
    Get utf8 text content of the file
    '''
    if self.mimetype == 'text/plain':
      with open(self.raw.path, 'r') as f:
        content = f.read()
    else:
      content = 'ciao'
  
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
    s = subprocess.check_output('ps aux | grep "%s"' % self.cmd, shell=True).split('\n')
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
    Ouptut None or the created job
    '''
    # check if there are job running...
    if Job.is_busy():
      return None
    if command not in ['harvest', 'whoosh']:
      # cpmmand stored into start
      popen_args = [settings.PYTHON_INTERPRETER, os.path.join(settings.BASE_DIR,'manage.py'), 'start', '--cmd', command, '--corpus']
    else:
      popen_args = [settings.PYTHON_INTERPRETER, os.path.join(settings.BASE_DIR,'manage.py'), command, '--corpus']
    logger.debug('starting cmd "%s"%s' % (command, ' as subprocess' if popen else '' ))
    job, created = Job.objects.get_or_create(corpus=corpus)
    job.status = Job.STARTED
    job.cmd = ' '.join(popen_args[:-1])
    job.save()

    popen_args.append(str(corpus.id))
    if popen:
      s = subprocess.Popen(popen_args, stdout=None, stderr=None)
      job.pid = s.pid
    else:
      job.pid = 0
    job.status=Job.RUNNING
    job.save()

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
  May contain something e.g to store a match result
  '''
  content = models.TextField()
  position = models.IntegerField()
  document =  models.ForeignKey(Document)