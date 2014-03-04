import re, os, signal, mimetypes, shutil, subprocess
from datetime import datetime 

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.dispatch import receiver



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



class Corpus(models.Model):
  name = models.CharField(max_length=32)
  slug = models.CharField(max_length=32, unique=True)
  date_created = models.DateTimeField(auto_now=True)
  date_last_modified = models.DateTimeField(auto_now_add=True)

  owners = models.ManyToManyField(User)


  def get_path(self):
    return os.path.join(settings.MEDIA_ROOT, self.slug)


  def save(self, **kwargs):
    self.slug = helper_uuslug(model=Corpus, instance=self, value=self.name)
    path = self.get_path()
    if not os.path.exists(path):
      os.makedirs(path)
    super(Corpus, self).save()


  def __unicode__(self):
    return '%s [%s]' % (self.name, self.slug)


  def json(self, deep=False):
    d = {
      'id': self.id,
      'name': self.name,
      'slug': self.slug
    }
    if deep:
      d.update({
        'owners': [helper_user_to_dict(u) for u in self.owners.all()]
      })
    return d



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

  EN = 'en',
  FR = 'fr',
  NL = 'nl'

  LANGUAGE_CHOICES = (
    (EN, u'english'),
    (FR, u'french'),
    (NL, u'dutch'),
  )

  content = models.CharField(max_length=128)
  lemmata = models.CharField(max_length=128)
  cluster = models.CharField(max_length=128) # index by cluster

  language  = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
  status    = models.CharField(max_length=3, choices=STATUS_CHOICES, default=IN)
  
  partofspeech = models.CharField(max_length=3, choices=POS_CHOICES)
  

  def __unicode__(self):
    return '%s [%s]' % (self.content, self.lemmata)


  def json(self, deep=False):
    d = {
      'content': self.content
    }
    return d


  class Meta:
    unique_together = ('content', 'language', 'partofspeech')



class Document(models.Model):
  name = models.CharField(max_length=128)
  slug = models.CharField(max_length=128, unique=True)
  corpus = models.ForeignKey(Corpus, related_name='documents')
  
  raw  = models.FileField(upload_to=helper_get_document_path, blank=True, null=True)
  mimetype = models.CharField(max_length = 100)

  date_created = models.DateTimeField(auto_now=True)
  date_last_modified = models.DateTimeField(auto_now_add=True)

  segments = models.ManyToManyField(Segment, through="Document_Segment", blank=True, null=True)


  def json(self, deep=False):
    d = {
      'id': self.id,
      'name': self.name,
      'slug': self.slug,
      'date_created': self.date_created.isoformat(),
      'date_last_modified': self.date_last_modified.isoformat()
    }
    
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


  def is_alive(self):
    s = subprocess.check_output('ps aux | grep "%s"' % self.cmd, shell=True).split('\n')
    print s
    for g in s:
      if re.search(r'\d\s%s' % self.cmd, g) is None:
        return True
    return False


  @staticmethod
  def is_busy():
    print 'is busy???'
    running_jobs = Job.objects.filter(status__in=[Job.RUNNING, Job.STARTED])
    print running_jobs.count()
    if running_jobs.count() > 0:
      for r in running_jobs:
        if r.is_alive():
          return False
        else:
          r.status = Job.LOST
          r.save()
      # if reached the end of the loop, all running job found are lost... so Job can do something again!
      return True
    else:
      return False


  @staticmethod
  def start(corpus, command='harvest'):
    '''
    Check if there are jobs running, otherwise
    Ouptut None or the created job
    '''
    # check if there are job running...
    if Job.is_busy():
      return None
    popen_args = [settings.PYTHON_INTERPRETER, os.path.join(settings.BASE_DIR,'manage.py'), command, '--corpus']
    
    job = Job(corpus=corpus, status=Job.STARTED, cmd=' '.join(popen_args[:-1]))
    job.save()

    popen_args.append(str(job.id))

    print job.cmd

    s = subprocess.Popen(popen_args, stdout=None, stderr=None)
    job.pid = s.pid
    job.status=Job.RUNNING
    job.save()

    return job


  def stop(self):
    os.kill(self.pid, signal.SIGKILL)
    self.status=Job.COMPLETED
    self.save()



class Document_Segment( models.Model ):
  document = models.ForeignKey(Document)
  segment = models.ForeignKey(Segment)

  tf = models.FloatField(default=0) # term normalized frequency of the stemmed version of the segment
  tfidf = models.FloatField( default=0) # inversed term calculated according to the document via the stemmed version
  wf = models.FloatField(default=0) # sublinear tf scaling (normalized on logarithm) = log(tf) if tf > 0
  tfidf = models.FloatField( default=0) # inversed term calculated according to the document via the stemmed version
  

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