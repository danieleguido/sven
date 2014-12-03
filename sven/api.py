#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess, logging, math, langid, json
from datetime import datetime
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db.models import Q, Count, Min, Max
from django.db import connection, transaction

from glue import Epoxy, API_EXCEPTION_AUTH, API_EXCEPTION_FORMERRORS, API_EXCEPTION_DOESNOTEXIST
from glue.api import edit_object

from sven.forms import LoginForm, CorpusForm, DocumentForm, CorpusSegmentForm, ProfileForm, TagsForm, UploadCSVForm

from sven.models import helper_truncatesmart
from sven.models import Corpus, Document, Document_Segment, Profile, Job, Segment, Tag, helper_get_document_path


logger = logging.getLogger("sven")

   

def home(request):
  '''
  Help or manual should be placed here
  '''
  result = Epoxy(request)
  return result.json()


@login_required(login_url='/api/login')
def notification(request):
  '''
  Tail
  '''
  epoxy = Epoxy(request)
  epoxy.meta('profile', request.user.profile.json())
    
  #try:
  #  epoxy.add('log', subprocess.check_output(["tail", settings.LOG_FILE], close_fds=True))
  #except OSError, e:
  #  logger.exception(e)
  # DEPRECATED. too much. 
  corpora = Corpus.objects.filter(owners=request.user)
  jobs = Job.objects.filter(corpus__owners=request.user)
  

  epoxy.queryset(corpora)
  try:
    epoxy.add('jobs', [j.json() for j in jobs])
  except Document.DoesNotExist, e:
    epoxy.add('jobs', [])

  epoxy.add('datetime', datetime.now().isoformat())

  return epoxy.json()



def not_found(request):
  '''
  Help or manual should be placed here
  '''
  result = Epoxy(request)
  result.throw_error(error='function does not exist')
  return result.json()


@csrf_exempt
def require_login(request):
  '''
  Help or manual should be placed here
  '''
  if request.user.is_authenticated():
    return home(request)

  epoxy = Epoxy(request)
  
  if epoxy.is_GET():
    return epoxy.throw_error(error='unauthenticated', code=API_EXCEPTION_AUTH).json()
  
  form = LoginForm(epoxy.data)
  if not form.is_valid():
    return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()

  user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
  if user is not None:
    if user.is_active:
      login(request, user)
      return home(request)
    else:
      return epoxy.throw_error(error='wrong credentials', code=API_EXCEPTION_AUTH).json()
  else:
    return epoxy.throw_error(error='wrong credentials', code=API_EXCEPTION_AUTH).json()
  
  if not request.POST.get('remember_me', None):
    request.session.set_expiry(0)


  return epoxy.json()



def login_view(request):
  if request.user.is_authenticated():
    return home(request)

  form = LoginForm(request.POST)
  next = request.REQUEST.get('next', 'sven_home')

  login_message = {
    'next': next if len( next ) else 'sven_home'
  }

  if request.method != 'POST':
    d = _shared_context(request, tags=[ "login" ], d=login_message)
    return render_to_response('sven/login.html', RequestContext(request, d ))

  if not request.POST.get('remember_me', None):
    request.session.set_expiry(0)

  if form.is_valid():
    user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
    if user is not None:
      if user.is_active:
        login(request, user)
        # @todo: Redirect to next page

        return redirect(login_message['next'])
      else:
        login_message['error'] = _("user has been disabled")
    else:
      login_message['error'] = _("invalid credentials")
      # Return a 'disabled account' error message
  else:
    login_message['error'] = _("invalid credentials")
    login_message['invalid_fields'] = form.errors
  
  d = _shared_context( request, tags=[ "login" ], d=login_message )
  return render_to_response('sven/login.html', RequestContext(request, d ) )



def require_logout( request ):
  logout( request )
  epoxy = Epoxy(request)
  return epoxy.json()



@login_required(login_url='/api/login')
def start(request, corpus_pk, cmd):
  '''
  Usage url: 
  '''
  epoxy = Epoxy(request)

  try:
    c = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  logger.debug('starting "%s" on corpus %s' % (cmd, corpus_pk))

  job = Job.start(corpus=c, command=cmd)
  if job is not None:
    epoxy.item(job)
  else:
    return epoxy.throw_error(error='a job is already running', code='BUSY').json()

  return epoxy.json()



@login_required(login_url='/api/login')
def corpus_documents(request, corpus_pk):
  '''
  sample request you can test with on localhost:
  http://localhost:8000/api/corpus/4/document?method=POST&tags=[{"type":"tm","tags":["primary media","secondary media"]}]&name=Test&indent&mimetype=text/plain&date=2014-09-24
  '''
  epoxy = Epoxy(request)
  logger.debug('corpus_documents')
  try:
    c = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    logger.exception(e)
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  if epoxy.is_POST(): # add a new document and attach it to this specific corpus. Content would be attached later, via upload. @todo
    candidates_tags = None
    # tags have to be a json oject
    if 'tags' in epoxy.data:
      try:
        candidates_tags = json.loads(epoxy.data['tags'])
      except ValueError, e:
        return epoxy.throw_error(error='json ValueError for tags param. %s'%e, code=API_EXCEPTION_FORMERRORS).json()
      except TypeError, e:
        candidates_tags = epoxy.data['tags']
        
      for t in candidates_tags:
        print t
        tagsform = TagsForm({'type':t['type'], 'tags': ' '.join(t['tags'])})
      #tagsform = TagsForm()
        if not tagsform.is_valid():
          return epoxy.throw_error(error=tagsform.errors, code=API_EXCEPTION_FORMERRORS).json()
        epoxy.meta('tags', candidates_tags)

    form = DocumentForm(epoxy.data)

    with transaction.atomic():
      if form.is_valid():
        # save tags
        tags = []
        if candidates_tags:
          for candidate_type in candidates_tags:
            for tag in candidate_type['tags']:
              t, created = Tag.objects.get_or_create(type=candidate_type['type'], name=tag[:128])
              tags.append(t)
        #save documents and attach tags
        d = form.save(commit=False)
        d.corpus = c
        d.save()

        d.tags.add(*tags)
        d.save()
        epoxy.item(d, deep=False)
      else:
        return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()

  logger.info("corpus document")
  try:
    epoxy.queryset(Document.objects.filter(corpus=c))
  except Exception, e:
    logger.exception(e)
    
  return epoxy.json()



@login_required(login_url='/api/login')
def documents(request):
  epoxy = Epoxy(request)
  epoxy.queryset(Document.objects.filter(corpus__owners=request.user))
  return epoxy.json()



@login_required(login_url='/api/login')
def document(request, pk):
  epoxy = Epoxy(request)
  
  try:
    d = Document.objects.get(pk=pk, corpus__owners=request.user)
  except Document.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()
  
  if epoxy.is_GET():
    epoxy.item(d, deep=True)
    return epoxy.json()
  
  if epoxy.is_DELETE():
    try:
      d.delete()
      epoxy.meta('total_count', Document.objects.filter(corpus__owners=request.user).count())
    except Exception,e:
      logger.exception(e)
      return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_FORMERRORS).json()
    return epoxy.json()

  if epoxy.is_POST(): # add a new document and attach it to this specific corpus. Content would be attached later, via upload. @todo
    form = edit_object(instance=d, Form=DocumentForm, epoxy=epoxy)
    if not form.is_valid():
      return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()
    d.save()
    # chec if there is a text param to save ...
    if 'text' in epoxy.data:
      logger.debug('saving text for the given document')
      d.set_text(epoxy.data['text'])
      epoxy.item(d, deep=True)
    else:
      epoxy.item(d, deep=False)
    
  return epoxy.json()



@login_required(login_url='/api/login')
def document_segments(request, pk):
  epoxy = Epoxy(request)
  try:
    d = Document.objects.get(pk=pk, corpus__owners=request.user)
  except Document.DoesNotExist, e:
    return result.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()
  
  # total count
  cursor = connection.cursor()
  cursor.execute("""
    SELECT
      COUNT(distinct cluster)
    FROM sven_segment s
      JOIN sven_document_segment ds ON s.id = ds.segment_id 
      WHERE ds.document_id = %(document_id)s
    """ % {
      'document_id': d.id
  })
  row = cursor.fetchone()
  epoxy.meta('total_count', row[0]) # luster pagination

  segments = Segment.objects.raw("""
    SELECT 
      s.`id`, s.`content`,s.`language`, 
      s.`cluster`, s.`status`, 
      MAX( ds.`tfidf`) AS `tfidf`,
      MAX( ds.`tf`) AS `tf`,
      COUNT( DISTINCT ds.document_id) AS `distribution` 
    FROM sven_segment s
      JOIN sven_document_segment ds ON s.id = ds.segment_id 
      JOIN sven_document d ON ds.document_id = d.id
    WHERE d.id = %(document_id)s
    GROUP BY s.cluster
    ORDER BY %(order_by)s
    LIMIT %(offset)s, %(limit)s
    """ % {
      'document_id': d.id,
      'order_by': ','.join(epoxy.order_by),
      'offset': epoxy.offset,
      'limit': epoxy.limit
  })

  epoxy.add('objects', [{
    'id': s.id,
    'tf': s.tf,
    'tf_idf': s.tfidf,
    'status': s.status,
    'cluster': s.cluster,
    'distribution': s.distribution,
    'content': s.content
  } for s in segments])

  return epoxy.json()



@login_required(login_url='/api/login')
def document_upload(request, corpus_pk):
  '''
  Create a document on upload.
  '''
  epoxy = Epoxy(request)
  try:
    corpus = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()
  import time, random
  time.sleep(random.randint(1,3))

  f = request.FILES['file']
  
  logger.info("%(user)s is uploading %(filename)s" % {
    'user': request.user.username,
    'filename':  f.name
  })

  d = Document(corpus=corpus, raw=f, name=f.name, abstract=Document.DOCUMENT_ABSTRACT_PLACEHOLDER)
  d.save()
  epoxy.meta('total_count', Document.objects.filter(corpus__owners=request.user).count())
  epoxy.item(d, deep=False)

  logger.info("%(user)s correctly uploaded %(filename)s" % {
    'user': request.user.username,
    'filename':  f.name
  })

  return epoxy.json()



@login_required(login_url='/api/login')
def document_text_version_download(request, pk):
  '''
  A special page to handle uploading of txt files
  for images and videos.
  '''
  try:
    doc = Document.objects.get(pk=pk, corpus__owners=request.user)
  except Document.DoesNotExist, e:
    return result.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()
  pass



@login_required(login_url='/api/login')
def document_text_version_upload(request, pk):
  '''
  A special page to handle uploading of txt files
  for images and videos.
  '''
  try:
    doc = Document.objects.get(pk=pk, corpus__owners=request.user)
  except Document.DoesNotExist, e:
    return result.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  f = request.FILES['file']

  # open file for writing.
  textified = '%s.txt' % doc.raw.path

  with open(textified, 'wb+') as destination:
    for chunk in f.chunks():
      destination.write(chunk)
  
  epoxy = Epoxy(request)
  epoxy.item(doc, True)
  return epoxy.json()



@login_required(login_url='/api/login')
def tags(request):
  epoxy = Epoxy(request)
  epoxy.queryset(Tag.objects.filter())
  return epoxy.json()



@login_required(login_url='/api/login')
def document_tags(request, pk):
  epoxy = Epoxy(request)
  try:
    doc = Document.objects.get(pk=pk, corpus__owners=request.user)
  except Document.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  if epoxy.is_POST():
    is_valid, result = helper_free_tag(instance=doc, append=True, epoxy=epoxy)
    if not is_valid:
      return epoxy.throw_error(error=result, code=API_EXCEPTION_FORMERRORS).json()

  if epoxy.is_DELETE():
    is_valid, result = helper_detach_tag(instance=doc, append=True, epoxy=epoxy)
    if not is_valid:
      return epoxy.throw_error(error=result, code=API_EXCEPTION_FORMERRORS).json()


  epoxy.item(doc, deep=False)
  return epoxy.json()



@login_required(login_url='/api/login')
def corpora(request):
  epoxy = Epoxy(request)

  if epoxy.is_POST():
    form = CorpusForm(epoxy.data)
    if form.is_valid():
      corpus = form.save(commit=False)
      corpus.save()
      corpus.owners.add(request.user)
      corpus.save()
      epoxy.item(corpus)
    else:
      return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()

  epoxy.queryset(Corpus.objects.filter(owners__in=[request.user]))
  return epoxy.json()



def corpus(request, pk):
  epoxy = Epoxy(request)

  try:
    cor = Corpus.objects.get(pk=pk)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  if epoxy.is_DELETE():
    cor.delete()
  else:
    epoxy.item(cor, deep=True)
    
  return epoxy.json()



@login_required(login_url='/api/login')
def corpus_stopwords(request, corpus_pk):
  epoxy = Epoxy(request)
  try:
    cor = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  if epoxy.is_POST():
    if 'words' not in epoxy.data:
      return epoxy.throw_error(error='words param not found', code=API_EXCEPTION_FORMERRORS).json()
    # clean empty lines

    cor.set_stopwords(sorted(filter(None,[
      w.strip() for w in epoxy.data['words'].split('\n')
    ])))

  epoxy.add('objects', cor.get_stopwords())
  return epoxy.json()



@login_required(login_url='/api/login')
def corpus_segments(request, corpus_pk):
  '''
  Return the list of segments in a specific corpus (given by pk)
  '''
  epoxy = Epoxy(request)
  try:
    cor = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return result.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()
  
  if not epoxy.order_by:
    epoxy.order_by = ['tf DESC']

  # update when needed
  
  # translate orderby -tf, tf or -tfidf, tfidf


  # total count. It works.
  cursor = connection.cursor()
  cursor.execute("""
    SELECT
      COUNT(distinct cluster)
    FROM sven_segment s INNER JOIN sven_document_segment ds ON s.id = ds.segment_id
      WHERE corpus_id = %(corpus_id)s
    """ % {
    'corpus_id': cor.id
  })

  row = cursor.fetchone()
  epoxy.meta('total_count', row[0]) # luster pagination
  segments = Segment.objects.raw("""
    SELECT 
      s.`id`, s.`content`,s.`language`, 
      s.`cluster`, s.`status`, 
      MAX( ds.`tfidf`) AS `tfidf`,
      MAX( ds.`tf`) AS `tf`,
      COUNT(DISTINCT ds.document_id) AS `distribution` 
    FROM sven_segment s
      JOIN sven_document_segment ds ON s.id = ds.segment_id 
      JOIN sven_document d          ON ds.document_id = d.id
      JOIN sven_corpus c            ON d.corpus_id = c.id
    WHERE c.id = %(corpus_id)s
    GROUP BY s.cluster
    ORDER BY %(order_by)s
    LIMIT %(offset)s, %(limit)s
    """ % {
    'corpus_id': cor.id,
    'order_by': ','.join(epoxy.order_by),
    'offset': epoxy.offset,
    'limit': epoxy.limit
  })

  epoxy.meta('query', '%s' %segments.query)

  # for each segments, tf e tfidf value for each actor...
  clusters = [{
    'id': s.id,
    'tf': s.tf,
    'tf_idf': s.tfidf,
    'status': s.status,
    'cluster': s.cluster,
    'distribution': s.distribution,
    'content': s.content,
    'tags': []
  } for s in segments]

  # computate group limit and group offset
  g_offset = 0
  g_limit = 50
  
  # if goruping on TAG: get the grouping, with limit and offsets as well
  tags = Tag.objects.filter(tagdocuments__corpus=cor)[g_offset:g_offset+g_limit]
  groups = ['0']+[ '%s' % g.id for g in tags]

  epoxy.meta('ids', groups)

  segments_tags = Segment.objects.raw("""
    SELECT 
      s.`id`, s.cluster, dt.tag_id,
      MAX(ds.tf) as tf,
      MAX(ds.tfidf) as tf_idf
    FROM sven_segment s 
      JOIN sven_document_segment ds ON ds.segment_id = s.id
      JOIN sven_document_tags dt ON dt.document_id = ds.document_id
    WHERE s.corpus_id = %(corpus_id)s
      AND dt.tag_id IN ("%(tag_ids)s")
      AND s.cluster IN ("%(clusters_ids)s")
    GROUP BY dt.tag_id, s.cluster

    """ % {
      'corpus_id': cor.id,
      'tag_ids': '","'.join(groups),
      'clusters_ids': '","'.join([c['cluster'] for c in clusters])
    })



  tags_per_clusters = [{
    'id': t.tag_id,
    'tf': t.tf,
    'tf_idf': t.tf_idf,
    'cluster': t.cluster
  } for t in segments_tags];

  for c in clusters:
    for t in tags_per_clusters:
      if t['cluster'] == c['cluster']:
        c['tags'].append(t)


  epoxy.add('objects', clusters)
  epoxy.add('groups', [t.json() for t in tags])


  return epoxy.json()



@login_required(login_url='/api/login')
def corpus_segment(request, corpus_pk, segment_pk):
  '''
  Edit/view a segment in a specific corpus (given by pk)
  '''
  epoxy = Epoxy(request)
  try:
    c = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST)

  try:
    s = Segment.objects.get(pk=segment_pk)
  except Segment.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST)

  if epoxy.is_POST():
    form = CorpusSegmentForm(epoxy.data)
    if form.is_valid():
      status = form.cleaned_data['status']
      cluster = form.cleaned_data['cluster']
      Segment.objects.filter(corpus=c, cluster=s.cluster).update(status=status, cluster=cluster)
      #Segment.objects.filter(cluster=, documents)
      #form.cleaned_data['status'],form.cleaned_data['cluster']

      pass
    else:
      return epoxy.throw_error(error=form.errors,code=API_EXCEPTION_FORMERRORS).json()

  if not epoxy.order_by:
    epoxy.order_by = ['ds.`tf` DESC', 'ds.document_id DESC']

  # filter documents

  segments = Segment.objects.raw("""
    SELECT 
      s.`id`, s.`content`,s.`language`, 
      s.`cluster`, s.`status`, 
      ds.`tfidf`,
      ds.`tf`,
      ds.document_id
    FROM sven_segment s
      JOIN sven_document_segment ds ON s.id = ds.segment_id 
      JOIN sven_document d ON ds.document_id = d.id
      JOIN sven_corpus c ON d.corpus_id = c.id
    WHERE c.id = %s
      AND s.cluster = %s
      ORDER BY %s
      LIMIT %s, %s
    """,[c.id, s.cluster, ','.join(epoxy.order_by), epoxy.offset, epoxy.limit]
  )

  s = s.json()
  s.update({
    'aliases': [{
    'id': alias.id,
    'tf': alias.tf,
    'tfidf': alias.tfidf,
    'status': alias.status,
    'cluster': alias.cluster,
    'content': alias.content
    } for alias in segments]
  })

  epoxy.add('object', s)

  return epoxy.json()


def corpus_concepts(request, corpus_pk):
  '''
  Export filtered segments.
  Given by filters params as JSON - as usual, Filters need to be prefixed either with document__ or segment__ prefixes
  '''
  epoxy = Epoxy(request)
  try:
    cor = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST)

  clusters = Document_Segment.objects.filter(document__corpus=cor, segment__status=Segment.IN).filter(**epoxy.filters).order_by(*epoxy.order_by).values('segment__cluster').annotate(
    distribution=Count('document', distinct=True),
    tf=Max('tf'),
    tf_idf=Max('tfidf')
  )

  epoxy.meta('q', '%s'%clusters.query)

  clusters_objects = [c for c in clusters[epoxy.offset : epoxy.offset + epoxy.limit]]
  
  if 'group_by' in epoxy.data:
    # available data grouping (translations for MYSQL)
    DATE_GROUPING = {
      'Ym' : "%%Y-%%m"
    }
    epoxy.meta('grouping', epoxy.data['group_by']) 

    if epoxy.data['group_by'] in DATE_GROUPING.keys():
      
      # get all groupin possibilities according to date:
      groups_available = Document.objects.filter(corpus=cor).extra(
        select={'G': """DATE_FORMAT(date, "%s")""" % DATE_GROUPING[epoxy.data['group_by']]}
      ).values('G').annotate(distribution=Count('id'))
      
      # get groupings e.g value for groups for selected cluster only
      groups = Document_Segment.objects.filter(
        document__corpus=cor,
        segment__status='IN'
      ).filter(**epoxy.filters).filter(segment__cluster__in=[c['segment__cluster'] for c in clusters_objects]).extra(
        select={'G': """DATE_FORMAT(date, "%%Y-%%m")"""}
      ).order_by().values('G', 'segment__cluster').annotate(
        distribution=Count('document', distinct=True),
        tf=Max('tf'),
        tf_idf=Max('tfidf')
      )

    elif any(epoxy.data['group_by'] in t for t in Tag.TYPE_CHOICES):
      # get all groupin possibilities according to date:
      groups_available = Tag.objects.filter(
        tagdocuments__corpus=cor
      ).prefetch_related('tagdocuments').distinct().values('name', 'id', 'slug').annotate(
        distribution=Count('tagdocuments')
      )
      
      groups = Document_Segment.objects.filter(
        document__corpus=cor,
        segment__status=Segment.IN,
        document__tags__type=epoxy.data['group_by']
      ).filter(**epoxy.filters).filter(segment__cluster__in=[c['segment__cluster'] for c in clusters_objects]).extra(
        select={'G':'sven_tag.name'}).order_by().values('G', 'segment__cluster').annotate(
        distribution=Count('document', distinct=True),
        tf=Max('tf'),
        tf_idf=Max('tfidf')
      )

    if groups_available:
      #epoxy.meta('query', '%s' % groups.query)
      # format here your groups
      epoxy.add('groups', [g for g in groups_available])

      # find the right  matching the group name
      for cluster in clusters_objects:
        for g in groups:
          if g['segment__cluster'] == cluster['segment__cluster']:
            if not 'cols' in cluster:
              cluster['cols'] = []
            cluster['cols'].append(g)            

    else:
      epoxy.warning('grouping', 'grouping not recognized, should be one value among these (for tags): %s' % ','.join([t[0] for t in Tag.TYPE_CHOICES])) 
    
      #epoxy.add('groups', [g.json() for g in set([g['G'] for g in groups])])

  #outputting values
  epoxy.add('objects', clusters_objects)
  # get global min and global max for clusters
  epoxy.meta('bounds', Document_Segment.objects.filter(document__corpus=cor, segment__status='IN').aggregate(max_tf=Max('tf'), min_tf=Min('tf'), max_tfidf=Max('tfidf'), min_tfidf=Min('tfidf')))
  # get total number of clusters
  epoxy.meta('total_count', clusters.count())
  
  return epoxy.json()


def export_corpus_concepts(request, corpus_pk):
  '''
  export a huge csv containing all the filtered/sorted concept
  '''
  epoxy = Epoxy(request)
  try:
    cor = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST)

  clusters = Document_Segment.objects.filter(document__corpus=cor).filter(**epoxy.filters).order_by(*epoxy.order_by).values('segment__cluster').annotate(
    distribution=Count('document', distinct=True),
    tf=Max('tf'),
    tf_idf=Max('tfidf')
  )

  # prepare http respinse to send csv data
  import unicodecsv
  from django.http import HttpResponse

  response = HttpResponse(content_type='text/plain; charset=utf-8')
  writer = unicodecsv.DictWriter(response, fieldnames=clusters[0].keys() + ['content', 'status', 'ordering'], delimiter=',', encoding='utf-8')
  writer.writeheader()

  DATE_GROUPING = {
    'Ym' : "%%Y-%%m"
  }

  limit = 100
  loops = int(math.ceil(1.0*clusters.count() / limit))
  step = 0

  # print set by set
  for i in range(0, loops):
    clusterindex = {}

    # create a small index to recover computated data
    for c in clusters[i*limit:i*limit+limit]:
      clusterindex[c['segment__cluster']] = c
      clusterindex[c['segment__cluster']]['ordering'] = step # sort order
      step = step + 1
    # get group values for the indexed clusters only

    if 'group_by' in epoxy.data:
      if epoxy.data['group_by'] in DATE_GROUPING.keys():
        # available data grouping (translations for MYSQL ONLY !)
        groups_available = Document.objects.filter(corpus=cor).extra(
          select={'G': """DATE_FORMAT(date, "%s")""" % DATE_GROUPING[epoxy.data['group_by']]}
        ).values('G').annotate(distribution=Count('id'))
        print groups_available

    # get distinct segments matching the indexed clusters
    segments = Segment.objects.filter(cluster__in=clusterindex.keys()).order_by('cluster')
    
    # print lines
    for s in segments:
      if 'content' in clusterindex[s.cluster]: #clusters has already benn added
        clusterindex[s.cluster]['content'] = '%s|' % clusterindex[s.cluster]['content'], s.content

      clusterindex[s.cluster].update({
        'content': s.content,
        'status' : s.status
      })
      #print enriched_segment
      writer.writerow(clusterindex[s.cluster])

      

  
  return response  

  epoxy.meta('n', loops)

  return epoxy.json()




def export_corpus_documents(request, corpus_pk):
  '''
  Export corpus document metadata in a csv file
  Each column is a tag category and different tags are separed by a comma.
  '''
  epoxy = Epoxy(request)
  try:
    c = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST)

  import unicodecsv
  from django.http import HttpResponse

  if 'plain-text' not in request.REQUEST:
    response = HttpResponse(mimetype='text/csv; charset=utf-8')
    response['Content-Description'] = "File Transfer";
    response['Content-Disposition'] = "attachment; filename=%s.documents.csv" % c.name 
  
  else:
    response = HttpResponse(mimetype='text/plain; charset=utf-8')
  
  docs = Document.objects.filter(corpus=c).filter(**epoxy.filters)
  writer = unicodecsv.writer(response, delimiter=',', encoding='utf-8')
  # write headers
  writer.writerow([u'key', u'name', u'date', u'language'] + [u'%s' % label for t,label in Tag.TYPE_CHOICES] )
  
  for doc in docs:
    tags = {u'%s' % tag_type:[] for tag_type,tag_label in Tag.TYPE_CHOICES}
  
    for tag in doc.tags.all():
      if u'%s' % tag.type in tags:
        tags[u'%s' % tag.type].append(tag.name)
    row = [doc.id, doc.name, doc.date.strftime('%Y-%m-%d') if doc.date is not None else None, doc.language]

    for tag_type,tag_label in Tag.TYPE_CHOICES:
      row.append(','.join(tags[tag_type])) # comma separated

    writer.writerow(row)

  return response



def import_corpus_documents(request, corpus_pk):
  '''
  Given a valid csv, change docuemnt values accordingly.
  This view call the job 'import tags'. Cfr. management/start_job.py script for further information.
  '''
  epoxy = Epoxy(request)
  try:
    c = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s %s'%(corpus_pk, e), code=API_EXCEPTION_DOESNOTEXIST).json() # or you're not allowed to ...

  # the uploaded file
  if epoxy.is_POST():
    form = UploadCSVForm(request.POST, request.FILES)
    if form.is_valid():
      filepath = c.saveCSV(request.FILES['file'], prefix='metadata')
      # launch command
      job = Job.start(corpus=c, command='importtags', csv=filepath)
      if job is not None:
        epoxy.item(job)
      else:
        return epoxy.throw_error(error='a job is already running', code='BUSY').json()
    else:
      return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()
  else:
    pass  
  return epoxy.json()



def export_corpus_segments(request, corpus_pk):
  '''
  Return the list of segments in a specific corpus (given by pk)
  '''
  epoxy = Epoxy(request)
  try:
    cor = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return result.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()
  import unicodecsv
  from django.http import HttpResponse

  if not epoxy.order_by:
    epoxy.order_by = ['tf DESC']
  # total count
  cursor = connection.cursor()
  cursor.execute("""
    SELECT
      COUNT(distinct cluster)
    FROM sven_segment 
      WHERE corpus_id = %(corpus_id)s
    """ % {
    'corpus_id': cor.id
  })

  row = cursor.fetchone()
  epoxy.meta('total_count', row[0]) # luster pagination

  segments = Segment.objects.raw("""
    SELECT 
      s.`id`, s.`content`,s.`language`, 
      s.`cluster`, s.`status`, 
      MAX( ds.`tfidf`) AS `tfidf`,
      MAX( ds.`tf`) AS `tf`,
      COUNT(DISTINCT ds.document_id) AS `distribution` 
    FROM sven_segment s
      JOIN sven_document_segment ds ON s.id = ds.segment_id 
      JOIN sven_document d          ON ds.document_id = d.id
      JOIN sven_corpus c            ON d.corpus_id = c.id
    WHERE c.id = %(corpus_id)s
    GROUP BY s.cluster
    ORDER BY %(order_by)s
    """ % {
    'corpus_id': cor.id,
    'order_by': ','.join(epoxy.order_by)
  })
  #print '%s' %segments.query
  #epoxy.meta('query', '%s' %segments.query)

  # for each segments, tf e tfidf value for each actor...
  clusters = [{
    'id': s.id,
    'tf': s.tf,
    'tf_idf': s.tfidf,
    'status': s.status,
    'cluster': s.cluster,
    'distribution': s.distribution,
    'content': s.content
  } for s in segments]
  
  if 'plain-text' not in request.REQUEST:
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Description'] = "File Transfer";
    response['Content-Disposition'] = "attachment; filename=%s.concepts.csv" % cor.name 
  
  else:
    response = HttpResponse(content_type='text/plain; charset=utf-8')
  
  writer = unicodecsv.DictWriter(response, fieldnames=['id','tf','tf_idf','status','cluster','distribution','content'], delimiter=',', encoding='utf-8')
  writer.writeheader()

  for s in clusters:
    # writer.writerow(['_id', 'content', 'concept',  'distribution', 'status', 'max_tf', 'max_tfidf'])
    writer.writerow(s)
  # headers  
  #writer.writerow(['_id', 'content', 'concept',  'distribution', 'status', 'max_tf', 'max_tfidf'])

  #for s in ss:
  #  writer.writerow([  s.id, s.content, s.cluster, s.distro, s.status, s.max_tf, s.max_tfidf])
  
  return response



@login_required(login_url='/api/login')
def profile(request, pk=None):
  '''
  return authenticated user's profile.
  If user is staff he can see everything
  '''
  epoxy = Epoxy(request)

  try:
    pro = Profile.objects.get(user__pk=pk) if pk is not None and request.user.is_staff else request.user.profile
  except Profile.DoesNotExist, e:
    pro = Profile(user=request.user, bio="")
    pro.save()
  except Exception, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  if epoxy.is_POST():
    form = edit_object(instance=pro, Form=ProfileForm, epoxy=epoxy)
    if not form.is_valid():
      return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()
    
    if form.cleaned_data['firstname']:
      pro.user.first_name = form.cleaned_data['firstname']
    
    if form.cleaned_data['lastname']:
      pro.user.last_name = form.cleaned_data['lastname']
    
    pro.user.save()
    form.instance.save()


  return epoxy.item(pro, deep=True).json()



@login_required(login_url='/api/login')
def corpus_filters(request, corpus_pk):
  '''
  return corpus documents timeline, tags distribution etc...
  If user is staff he can see everything
  '''
  epoxy = Epoxy(request)
  filters = {'timeline': {}, 'tags':{}}

  try:
    c = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST)

  ids = []
  docs = helper_get_available_documents(request=request, corpus=c).filter(**epoxy.filters)
  
  for t in docs.order_by().values('date'):
    print t
    if t['date']:
      _date = t['date'].strftime('%Y-%m-%d')
    else:
      _date = datetime.today().strftime('%Y-%m-%d')

    if _date not in filters['timeline']:
      filters['timeline'][_date] = {
        'count' : 0,
        'value' : _date
      }

    filters['timeline'][_date]['count'] = filters['timeline'][_date]['count'] + 1
    

  # deal with reduce and search field
  if epoxy.reduce:
    for r in epoxy.reduce:
      docs = queryset.filter(r)

  if epoxy.search:
    docs = queryset.filter( Document.search(epoxy.search)).distinct()

  for d in docs:
    ids.append(d.id)

  epoxy.meta('filtered_count', len(ids))
  
  for chunk_ids in helper_chunk_list(ids, 50):
    
    for t in Tag.objects.filter(document__id__in=chunk_ids):
      _type = '%s' % t.type
      _slug = '%s' % t.slug

      if _type not in filters['tags']:
        filters['tags'][_type] = {}

      if _slug not in filters['tags'][_type]:
        filters['tags'][_type][_slug] = {
          'name': t.name,
          'slug': t.slug,
          'count': 0
        }

      filters['tags'][_type][_slug]['count'] += 1

  epoxy.add('objects', filters)
  return epoxy.json()



@login_required(login_url='/api/login')
def download(request, corpus_pk):
  pass



@login_required(login_url='/api/login')
def jobs(request):
  epoxy = Epoxy(request)
  epoxy.queryset(Job.objects.filter(corpus__owners=request.user))
  return epoxy.json()



@login_required(login_url='/api/login')
def job(request, corpus_pk, cmd):
  epoxy = Epoxy(request)
  epoxy.queryset(Job.objects.filter(corpus__owners=request.user))
  return epoxy.json()



@login_required(login_url='/api/login')
def d3_timeline(request):
  '''
  Format (filtered) document to be displayed with d3 datas.
  Cfr src/js/
  and 
  '''
  epoxy = Epoxy(request)
  values = {}
  warnings = 0;

  docs = helper_get_available_documents(request).filter(**epoxy.filters)
  epoxy.meta('total_count',docs.count())

  for t in docs.order_by().values('date'):
    if t['date']:
      _date = t['date'].strftime('%Y-%m-%d')
    
      if _date not in values:
        values[_date] = {
          'count' : 0,
          'value' : _date
        }
      values[_date]['count'] =  values[_date]['count'] + 1
    else:
      warnings = warnings + 1;

  values["1980-02-01"] = {'count': 7, 'value': "1980-02-01"}

  epoxy.add('values', values.values())
  epoxy.warning('no_datetime', warnings)
  return epoxy.json()



@login_required(login_url='/api/login')
def graph_corpus_tags(request, corpus_pk):
  '''
  corpus tags as nodes-edges value
  '''
  epoxy = Epoxy(request)
  epoxy.add('nodes', [t.json() for t in Tag.objects.filter(tagdocuments__corpus__pk=corpus_pk).distinct()])
  
  cursor = connection.cursor()
  # NODES
  cursor.execute("""
    SELECT t.id, t.name, t.slug, COUNT(*) as distribution
      FROM sven_tag t
    JOIN sven_document_tags dt
      ON t.id=dt.tag_id
    WHERE dt.document_id IN (
      SELECT d.id FROM sven_document as d WHERE d.corpus_id=%(corpus_pk)s
    ) GROUP BY t.id 
    """ % {
    'corpus_pk': corpus_pk
  })
  epoxy.add('nodes', [{
    'id':'d%s' % r[0],
    'label': r[1],
    'size': r[3]
  } for i,r in enumerate(cursor.fetchall())])

  return epoxy.json()




def helper_get_available_documents(request, corpus=None):
  '''
  Return a queryset according to user auth level and document status
  @param request
  @return <django.model.Queryset>
  '''
  if corpus is not None:
    if request.user.is_staff:
      queryset = Document.objects.filter(corpus=corpus).distinct()
    elif request.user.is_authenticated():
      queryset = Document.objects.filter(corpus=corpus)
    else:
      queryset = Document.objects.filter().distinct()
  else:
    queryset = Document.objects.filter(corpus__owners=request.user)
  return queryset



def helper_chunk_list(l, n):
    """
    Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
      yield l[i:i+n]



@transaction.atomic
def helper_free_tag(instance, epoxy, append=True):
  '''
  instance's model should have tags m2m property...
  '''
  form = TagsForm(epoxy.data)

  if form.is_valid():
    tags = list(set([t.strip() for t in form.cleaned_data['tags'].split(',')]))# list of unique comma separated cleaned tags.
    candidates = []
    for tag in tags:
      t, created = Tag.objects.get_or_create(name=tag, type=form.cleaned_data['type'])
      if append:
        instance.tags.add(t)
      else:
        candidates.append(t)

    if not append:
      instance.tags = candidates
    
    instance.save()

    return True, instance
  return False, form.errors



@transaction.atomic
def helper_detach_tag(instance, epoxy, append=True):
  '''
  instance's model should have tags m2m property...
  '''
  form = TagsForm(epoxy.data)

  if form.is_valid():
    tags = list(set([t.strip() for t in form.cleaned_data['tags'].split(',')]))# list of unique comma separated cleaned tags.
    candidates = []
    for tag in tags:
      try:
        t = Tag.objects.get(name=tag, type=form.cleaned_data['type'])
      except Tag.DoesNotExist, e:
        continue

      instance.tags.remove(t)
    
    instance.save()
    return True, instance
  return False, form.errors