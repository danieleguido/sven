import os, mimetypes
from datetime import datetime 

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify



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

  def json(self):
    d = {
      'pk': self.pk
    }
    return d


class Document(models.Model):
  name = models.CharField(max_length=128)
  slug = models.CharField(max_length=128, unique=True)
  corpus = models.ForeignKey(Corpus)
  
  raw  = models.FileField(upload_to=helper_get_document_path)
  mimetype = models.CharField(max_length = 100)

  date_created = models.DateTimeField(auto_now=True)
  date_last_modified = models.DateTimeField(auto_now_add=True)


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


  # segments = models.ManyToManyField(Segments, through="Document_Segment" ) # contains info about document term frequency
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

  cmd = models.TextField()
  corpus = models.ForeignKey(Corpus, unique=True)
  status = models.CharField(max_length=3, choices=STATUS_CHOICES, default=STARTED)
  completion = models.FloatField(default='0')

  date_created = models.DateTimeField(auto_now=True)
  date_last_modified = models.DateTimeField(auto_now_add=True)

  def get_pid(self):
    self.cmd
    pass

  def start(self):
    self.status=Job.STARTED
    self.save()
    pass

  def complete(self):
    self.status=Job.COMPLETED
    self.save()
    pass



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
  
  class Meta:
    unique_together = ('content', 'language', 'partofspeech')