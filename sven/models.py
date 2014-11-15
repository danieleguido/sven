#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math, re, os, signal, operator, mimetypes, shutil, urllib2, json, subprocess, logging, codecs
from datetime import datetime 

from django.conf import settings
from django.db import models, transaction, connection
from django.db.models import Q, Count
from django.db.models.signals import pre_delete, post_save
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils.timezone import make_aware, utc
from django.dispatch import receiver

from sven.distiller import dry, gooseapi, pdftotext, dictfetchall

logger = logging.getLogger("sven")



def helper_truncatesmart(value, limit=80):
    """
    Truncates a string after a given number of chars keeping whole words.
    
    Usage as templatetag:
        {{ string|truncatesmart }}
        {{ string|truncatesmart:50 }}
        # Join the words and return
    """
    value = unicode(value).strip() # Make sure it's unicode
    
    if len(value) <= limit:# Return the string itself if length is smaller or equal to the limit
      return value
    
    value = value[:limit] # Cut the string
    words = value.split(' ')[:-1] # Break into words and remove the last
    
    return ' '.join(words) + '...'



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

  date_created = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)


  def json(self, deep=False):
    d = {
      'id': self.id,
      'bio_raw': self.bio,
      'bio': self.bio,
      'picture': self.picture,
      'username': self.user.username,
      'firstname': self.user.first_name,
      'lastname': self.user.last_name,
      'date_created': self.date_created.isoformat(),
      'date_last_modified': self.date_last_modified.isoformat() if self.date_last_modified else None,
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

  date_last_modified = models.DateTimeField(auto_now=True)
  date_created = models.DateTimeField(auto_now_add=True)

  owners = models.ManyToManyField(User, related_name="corpora")
  watchers = models.ManyToManyField(User, related_name="corpora_watched")


  def get_path(self):
    return os.path.join(settings.MEDIA_ROOT, self.slug)


  def get_csv_path(self, language=None):
    '''
    return the destination path to store imported csv files.
    '''
    csv_path = os.path.join(settings.CSV_PATH, self.slug)
    if not os.path.exists(csv_path):
      os.makedirs(csv_path)

    return csv_path


  def saveCSV(self, f, prefix=''):
    '''
    return the absolute path of the saved csv file to be associated with import command
    '''
    filename = os.path.join(self.get_csv_path(), '%s.%s.csv' % (prefix,datetime.now().isoformat()))
    with open(filename, 'wb+') as destination:
      for chunk in f.chunks():
        destination.write(chunk)
    return filename
  

  def get_stopwords_path(self, language=None):
    stopwords_path = os.path.join(settings.STOPWORDS_PATH, self.slug)
    if not os.path.exists(stopwords_path):
       os.makedirs(stopwords_path)

    return os.path.join(stopwords_path, "%s.txt" % language if language else "all.txt")
    

  def get_stopwords(self, language=None):
    '''
    from the stopword path, add one stopwords per languages
    @param language if None, a generic stopword file will be associated.
    '''
    stopwords_filepath = self.get_stopwords_path(language)
    try:
      with open (stopwords_filepath, 'r+') as stopwords:
        data = stopwords.read().split('\n')
    except IOError, e:
      with open (stopwords_filepath, 'w+') as stopwords:
        data = ''
    return data


  def set_stopwords(self, contents=[], language=None):
    '''
    write stopword list file
    @param contents is a list of **unicode** string [u'ciao', u'mamma']
    '''
    stopwords_filepath = self.get_stopwords_path(language)
    with codecs.open(stopwords_filepath, encoding='utf-8', mode='w') as f:
      f.write("\n".join(contents))


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
      },
      'jobs': [j.json() for j in self.job.all()]
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
      # loading tags for venn diagram
      # t.documents.values() Tag.objects.filter(document__corpus=self)]
      d.update({
        'owners': [helper_user_to_dict(u) for u in self.owners.all()],

        'venn':{
          'sets': [
            {"label": "Radiohead", "size": 77348},
            {"label": "Thom Yorke", "size": 5621},
            {"label": "John Lennon", "size": 7773},
            {"label": "Kanye West", "size": 27053},
            {"label": "Eminem", "size": 19056},
            {"label": "Elvis Presley", "size": 15839},
            {"label": "Explosions in the Sky", "size": 10813},
            {"label": "Bach", "size": 9264},
            {"label": "Mozart", "size": 3959},
            {"label": "Philip Glass", "size": 4793},
            {"label": "St. Germain", "size": 4136},
            {"label": "Morrissey", "size": 10945},
            {"label": "Outkast", "size": 8444}
          ],
          'overlaps': [
            {"sets": [0, 1], "size": 4832},
            {"sets": [0, 4], "size": 2723},
            {"sets": [0, 5], "size": 3177},
            {"sets": [0, 6], "size": 5384},
            {"sets": [0, 7], "size": 2252},
          ]
        }
      })


    return d


  def tfidf(self):
    '''
    computate tfidf and wfidf calculation for every document in corpus
    '''
    number_of_documents = self.documents.count()
    number_of_segments  = self.segments.count()

    if number_of_documents == 0:
      raise Exception('not enough "documents" in corpus to perform tfidf')# @todo

    if number_of_segments == 0:
      raise Exception('not enough "segments" in corpus to perform tfidf')# @todo

    # 2. get all languages in corpus
    with transaction.atomic():
      number_of_languages = self.segments.values('language').distinct()
      
      # 3. start querying per language stats
      cursor = connection.cursor()
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
            self.id,
            language,
            Segment.IN
          ]
        )
        
        for i, cluster in enumerate(dictfetchall(cursor)):

          # for each cluster, calculate df value inside the overall corpus.
          df = float(cluster['distribution'])/number_of_documents
          
          # group by cluster and update value for the document_segment table. TFIDF is specific for each couple.
          for ds in Document_Segment.objects.filter(segment__cluster=cluster['cluster'], segment__language=language):
            ds.tfidf = ds.tf * math.log(1/df) 
            ds.wfidf = ds.wf * math.log(1/df)
            print i, cluster['cluster'], df, ds.tf, ds.tfidf
            ds.save()

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
  TYPE_OF_MEDIA = 'tm'

  ALCHEMY = {
    'City':'Ci'
  }
  
  TYPE_CHOICES = (
    (FREE, 'tags'),
    (TYPE_OF_MEDIA, 'type_of_media'),
    (ACTOR, 'actor'),
    (INSTITUTION, 'institution'),
  )

  OEMBED_PROVIDER_NAME = 'OP' #tag specify an oembed field...
  OEMBED_TITLE = 'OT' #tag specify an oembed field...
  OEMBED_URL = 'OU'
  OEMBED_THUMBNAIL_URL = 'OH'
  OEMBED_VIDEO_ID = 'OI'
  OEMBED_HEIGHT = 'Oh'
  OEMBED_WIDTH = 'Ow'

  TYPE_OEMBED_CHOICES = (
    (OEMBED_PROVIDER_NAME, 'oembed_provider_name'),
    (OEMBED_TITLE, 'oembed_title'),
    (OEMBED_URL, 'oembed_url'),
    (OEMBED_THUMBNAIL_URL, 'oembed_thumbnail_url'),
    (OEMBED_VIDEO_ID, 'oembed_video_id'),
    (OEMBED_HEIGHT, 'oembed_height'),
    (OEMBED_WIDTH, 'oembed_width'),
  )

  name = models.CharField(max_length=128) # e.g. 'Mr. E. Smith'
  slug = models.SlugField(max_length=128, unique=True) # e.g. 'mr-e-smith'
  type = models.CharField(max_length=2, choices=TYPE_CHOICES + TYPE_OEMBED_CHOICES, default=FREE) # e.g. 'actor' or 'institution'


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
  abstract = models.CharField(max_length=160,  blank=True, null=True) # sample taken from .text() transformation 
  corpus = models.ForeignKey(Corpus, related_name='documents')
  
  language  = models.CharField(max_length=2, choices=settings.LANGUAGE_CHOICES)

  raw  = models.FileField(upload_to=helper_get_document_path, blank=True, null=True)
  mimetype = models.CharField(max_length=100)



  date = models.DateTimeField(blank=True, null=True)
  date_created = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)
  
  url = models.URLField(blank=True, null=True, max_length=255) # external url to be boilerplated

  segments = models.ManyToManyField(Segment, through="Document_Segment", blank=True, null=True)
  tags = models.ManyToManyField(Tag, blank=True, null=True)


  def json(self, deep=False):
    d = {
      'id': self.id,
      'name': self.name,
      'slug': self.slug,
      'abstract': self.abstract,
      'mimetype': self.mimetype,
      'language': self.language,
      'date': self.date.strftime("%Y-%m-%d") if self.date else None,
      'date_created': self.date_created.isoformat(),
      'date_last_modified': self.date_last_modified.isoformat(),
      'tags': {},
      'url': self.url
      #[t.json() for t in self.tags.all()]
    }

    for t in self.tags.all():
      k = t.get_type_display()
      if t.type in [Tag.OEMBED_PROVIDER_NAME, Tag.OEMBED_VIDEO_ID]:
        d['tags'][k] = t.json()
        continue
      if k not in d['tags']:
        d['tags'][k] = []

      d['tags'][k].append(t.json())

    if self.raw:
      if self.mimetype != "text/plain":
        d['media'] = os.path.join(settings.MEDIA_URL, self.corpus.slug, os.path.basename(self.raw.url))
        d['media_txt'] = os.path.join(settings.MEDIA_URL, self.corpus.slug, os.path.basename(self.raw.url))+'.txt'
      else:
        d['media_txt'] = os.path.join(settings.MEDIA_URL, self.corpus.slug, os.path.basename(self.raw.url))

    elif self.mimetype == "text/html":
      d['media_txt'] = os.path.join(settings.MEDIA_URL, self.corpus.slug, self.slug) + '.txt'
    
    if deep:
      d['corpus'] = self.corpus.json()
      try:
        d.update({
          'text': self.text()[:25000],
          'language': self.language
        })
      except UnicodeDecodeError, e:
        d.update({
          'text': 'can\'t get the text version of this document: %s' % e
        })
      except Exception, e:
        logger.exception(e)
        d.update({
          'text': 'can\'t get the text version of this document %s' % e
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
  def indexed_search(query, epoxy, queryset):
    '''
    test: http://localhost:8000/api/corpus/1/document?search=king&indent
    '''
    from whoosh.qparser import QueryParser
    from whoosh.query import Term, Or
    ix = Document.get_whoosh()
    parser = QueryParser("content", ix.schema)
    q = parser.parse(query)

    qs = queryset.filter(**epoxy.filters)
    ids = [u'%s' % d.id for d in qs]

    print qs.count()
    restrict_q = Or([Term("path", u'%s' % d.id) for d in qs])# [Term("path", u'1'), Term("path", u'3')])

    with ix.searcher() as searcher:
    #results = s.search(q)
      results = searcher.search(q, limit=200, filter=restrict_q)
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
    Get utf8 text content of the file. If the document is of type text/html
    '''
    if self.mimetype is None:
      content = "" # not yet ready ... Empty string
    elif self.mimetype == 'text/plain':
      with codecs.open(self.raw.path, encoding='utf-8', mode='r') as f:
        content = f.read()
    else: #document which need textification
      textified = '%s.txt' % self.raw.path if self.raw else '%s/%s.txt' % (self.corpus.get_path(), self.slug)
      
      if os.path.exists(textified):
        with codecs.open(textified, encoding='utf-8', mode='r') as f:
          content = f.read()

      else: # content needs to b created
        if self.mimetype == "application/pdf":
          content = pdftotext(self.raw.path)
          with codecs.open(textified, encoding='utf-8', mode='w') as f:
            f.write(content)
        elif self.url is not None:
          try:
            goo = gooseapi(url=self.url) # use gooseapi to extract text content from html
          except urllib2.HTTPError,e:
            logger.error('HTTPError received while goosing %s' % url)
            logger.exception(e)
            content = ''
          else:
            content = goo.cleaned_text
            with codecs.open(textified, encoding='utf-8', mode='w') as f:
              f.write(content)
        else:
          content = '' #%s does not have a text associed. %s' % (self.mimetype, textified)
        # exitsts text translations?
        
        # store whoosh, only if contents needs to be created. not that store update document content in index
        if len(content):
          self.store(content)

    if not self.language:
      import langid
      self.abstract = helper_truncatesmart(content, 150)
      language, probability = langid.classify(content[:255])
      self.language = language
      self.save()
    
    content = dry(content)
    return content


  def set_text(self, content):
    textified = '%s.txt' % self.raw.path if self.raw else '%s/%s.txt' % (self.corpus.get_path(), self.slug)
    with codecs.open(textified, encoding='utf-8', mode='w') as f:
      f.write(content)
    return content


  def autotag(self):
    '''
    DEPRECATED as UNUSED
    Perform autotagging by using alchemyapi.
    Note: Settings.ALCHEMYAPI_KEY var should be set !

    '''
    if settings.ALCHEMYAPI_KEY is not None:
      from distiller import alchemyapi
      res = alchemyapi(api_key=settings.ALCHEMYAPI_KEY, text=self.text()[:100000])
      for ent in res['entities'][:5]:
        # max 5 entities
        print ent
        t, created = Tag.objects.get_or_create(type=Tag.ACTOR, name='%s - %s' % (ent['text'], ent['type']))
        self.tags.add(t)
    


  def store(self, content):
    ix = Document.get_whoosh()
    writer = ix.writer() # multi thread cfr. from whoosh.writing import AsyncWriter

    writer.update_document(
      title = self.name,
      path = u"%s"%self.id,
      content = content)
    writer.commit()


  def save(self, **kwargs):
    # understanding datetime included in file title... YYYY MM DD
    date = re.search(r'_(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})_',self.name)
    if not self.date and date:
      self.date = make_aware(datetime.strptime('%s-%s-%s' % (date.group('year'), date.group('month'), date.group('day')), '%Y-%m-%d'), utc)

    self.slug = helper_uuslug(model=Document, instance=self, value=self.name)
    if self.raw:
      self.mimetype = mimetypes.guess_type(self.raw.path)[0]

    if self.url: # load metadata if is a oembed service.
      import micawber
      mic = micawber.bootstrap_basic()
      # add issuu rule...?
      try:
        oem = mic.request(self.url)
      except micawber.exceptions.ProviderNotFoundException, e:
        pass
      else: # store as oembed tags
        if not self.id:
          """
          oem sample: 
          {u'is_plus': u'0', u'provider_url': u'https://vimeo.com/', u'description': u'McTAVISH - Dedicated to the Craft Series\n\nDirected, Filmed & Edited:\nStefan Jos\xe9\nwww.stefanjosefilms.com\n@stefanjosefilms\n\nCompelled to spend his entire life riding waves Bob McTavish started building surfboards in 1962. Today, over 50 years later, his vision is alive and well at the McTavish Factory in Byron Bay, Australia.\nThis collection of portraits gives a glimpse into the people and moments that are ... dedicated to the craft.\n\nEpisode Two:\nSurfer: Christian Barker\nMusic: MT Warning\n\nmctavish.com.au\n@mctavishsurf', u'uri': u'/videos/105104354', u'title': u"MCTAVISH - 'Dedicated to the Craft Series'  Episode two:  Christian Barker", 'url': u'http://vimeo.com/105104354', u'video_id': 105104354, u'html': u'<iframe src="//player.vimeo.com/video/105104354" width="1280" height="546" frameborder="0" title="MCTAVISH - &#039;Dedicated to the Craft Series&#039;  Episode two:  Christian Barker" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>', u'author_name': u'Stefan Jos\xe9 Films', u'height': 546, u'thumbnail_width': 1280, u'width': 1280, u'version': u'1.0', u'author_url': u'http://vimeo.com/stefanjosefilms', u'duration': 367, u'provider_name': u'Vimeo', u'thumbnail_url': u'http://i.vimeocdn.com/video/487826345_1280.jpg', u'type': u'video', u'thumbnail_height': 546}
          """
          self.name = oem['title']
          super(Document, self).save()

        with transaction.atomic():
          for tag_type, tag_type_value in Tag.TYPE_OEMBED_CHOICES: # e.g. 'OP' 'oembed_provider_name'
            oembed_key = tag_type_value.split('_',1).pop() # eg 'provider_name' from 'oembed_provider_name'
            if oembed_key in oem:
              t, created = Tag.objects.get_or_create(type=tag_type, name=u'%s'%oem[oembed_key])
              self.tags.add(t)

    super(Document, self).save()



class Job(models.Model):
  STARTED = 'BOO'
  RUNNING = 'RUN'
  LOST = 'RIP'
  COMPLETED = 'END'
  ERROR = 'ERR'

  STATUS_CHOICES = (
    (STARTED, u'started'),
    (RUNNING, u'running'),
    (LOST, u'process not found'),
    (COMPLETED, u'job completed'),  
    (ERROR, u'job error') ,
  )

  pid = models.CharField(max_length=32)
  cmd = models.TextField()
  corpus = models.ForeignKey(Corpus, unique=True, related_name='job')
  document = models.ForeignKey(Document, null=True, blank=True) # current working on document...

  status = models.CharField(max_length=3, choices=STATUS_CHOICES, default=STARTED)
  completion = models.FloatField(default='0')

  date_created = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)


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
  def start(corpus, command='harvest', csv='', popen=True):
    '''
    Check if there are jobs running, otherwise
    Ouptut None or the created job.
    Test with:
    http://localhost:8000/api/corpus/1/start/harvest
    http://localhost:8000/api/corpus/1/start/whoosher
    '''

    # check if there are similar job running...
    #if Job.is_busy():
    #  logger.debug('job is busy %s , you need to wait for your turn...' % command)
    #  return None
    running_jobs = Job.objects.filter(status__in=[Job.RUNNING, Job.STARTED])
    if running_jobs.count() > 0:
      logger.debug('ouch, your corpus is busy in doing something else ...')
      return None
    # creating corpus related job
    job, created = Job.objects.get_or_create(corpus=corpus)
    job.status = Job.RUNNING
    job.completion = 0
    # set as default
    logger.debug('init start "%s"' % command) 
    popen_args = [
      settings.PYTHON_INTERPRETER, # the virtualenv python
      os.path.join(settings.BASE_DIR, 'manage.py'), # local manage script
      'start_job', 
      '--cmd', command,
      '--job', str(job.pk),
      '--csv', str(csv)
    ]

    
    s = subprocess.Popen(popen_args, stdout=None, stderr=None, close_fds=True)
    job.cmd = ' '.join(popen_args)
    logger.debug('cmd "%s"' % job.cmd) 
    job.pid = s.pid
    job.save()

    return job

    print popen_args
    

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
    #if self.pid != 0:
    #  logger.debug('killing pid %s' % int(self.pid))
    #  try:
    #    os.kill(int(self.pid), signal.SIGKILL)
    #  except OSError, e:
    #    logger.exception(e)
    # everything below will not be executed, since the process id has benn killed.


  def json(self, deep=False):
    d = {
      'cmd': self.cmd,
      'completion': self.completion,
      'document': self.document.json() if self.document else '',
      'id': self.id,
      'pid': self.pid,
      'status': self.status
    }
    return d


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



class DocumentInfo(models.Model):
  '''
  This class is a good companion for Document: here will be held everythingstatus or boolean information
  '''
  document = models.OneToOneField(Document, related_name="info")
  
  date_last_modified = models.DateTimeField(auto_now=True)

  date_indexed  = models.DateTimeField(blank=True, null=True) # None = not set, false = No, tru = Set
  date_deleted  = models.DateTimeField(blank=True, null=True) # true here means recovered?
  date_texified = models.DateTimeField(blank=True, null=True) #useful for texified documents
  date_analyzed = models.DateTimeField(blank=True, null=True)



@receiver(post_save, sender=Document)
def create_document_info(sender, instance, created, **kwargs):
  if created:
    dif = DocumentInfo(document=instance)
    dif.save()



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

