#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re, os, subprocess, logging, math, langid, json
from datetime import datetime
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from django.db import connection, transaction
from django.db.models import Q, Count, Min, Max, Aggregate
from django.db.models.sql.aggregates import Aggregate as SQLAggregate

from glue import Epoxy, API_EXCEPTION_AUTH, API_EXCEPTION_FORMERRORS, API_EXCEPTION_DOESNOTEXIST
from glue.api import edit_object

from sven.forms import LoginForm, CorpusForm, DocumentForm, CorpusSegmentForm, ProfileForm, TagsForm, UploadCSVForm

from sven.models import helper_truncatesmart
from sven.models import Corpus, Document, Document_Segment, Profile, Job, Segment, Tag, helper_get_document_path

import networkx as nx
from networkx.readwrite import json_graph
from networkx.algorithms import bipartite

logger = logging.getLogger("sven")

DATE_GROUPING = {
  'Y': "%%Y",
  'Ym' : "%%Y-%%m",
  'Ymd' : "%%Y-%%m-%%d"
}


# SPECIQL aggregation class for MYSQL
class SQLConcat(SQLAggregate):
  name = 'GROUP_CONCAT'
  sql_function = 'GROUP_CONCAT'
  sql_template = '%(function)s(DISTINCT %(field)s SEPARATOR "%(separator)s")'

# print cluster_filters
class GroupConcat(Aggregate):
  def add_to_query(self, query, alias, col, source, is_summary):
    aggregate = SQLConcat(col, source=source, is_summary=is_summary, **self.extra)
    query.aggregates[alias] = aggregate
  

def jaccard(G, u, v):
  # given a graph G, calculate the jaccard distance u-v
  unbrs = set(G[u])
  vnbrs = set(G[v])
  return 1-float(len(unbrs & vnbrs)) / len(unbrs | vnbrs)



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
  # available tags categories. to be cached somehow
  tags = Tag.objects.filter(tagdocuments__corpus__owners=request.user).values('type').annotate(count=Count('id'))

  epoxy.queryset(corpora)
  # print [j.json() for j in corpora]

  try:
    epoxy.add('jobs', [j.json() for j in jobs])
  except Document.DoesNotExist, e:
    epoxy.add('jobs', [])

  epoxy.add('tags', [t for t in tags])
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

  # filter cmd by user
  if cmd in settings.ADMIN_COMMANDS and not request.user.is_staff:
    return epoxy.throw_error(error='Not authorized', code=API_EXCEPTION_AUTH).json()

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
def corpus_tags(request, corpus_pk):
  '''
  return corpus related tags
  '''
  epoxy = Epoxy(request)
  # create tag if request is POST request
  if epoxy.is_POST():
    pass
  
  epoxy.queryset(Tag.objects.filter(tagdocuments__corpus__owners=request.user, tagdocuments__corpus__pk=corpus_pk).distinct())
  return epoxy.json()


@login_required(login_url='/api/login')
def corpus_documents(request, corpus_pk):
  '''
  sample request you can test with on localhost:
  http://localhost:8000/api/corpus/4/document?method=POST&tags=[{"type":"tm","tags":["primary media","secondary media"]}]&name=Test&indent&mimetype=text/plain&date=2014-09-24
  '''
  epoxy = Epoxy(request)
  
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
        # print t
        tagsform = TagsForm({'type':t['type'], 'tags': ' '.join(t['tags'])})
      #tagsform = TagsForm()
        if not tagsform.is_valid():
          return epoxy.throw_error(error=tagsform.errors, code=API_EXCEPTION_FORMERRORS).json()
        epoxy.meta('tags', candidates_tags)


    form = DocumentForm(epoxy.data)

    if not form.is_valid():
      return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()

    if 'url' in form.cleaned_data and Document.objects.filter(corpus=c, url=form.cleaned_data['url']).count() > 0:
      # check for url uniqueness
      return epoxy.throw_error(error={'url':['url exists already']}, code=API_EXCEPTION_FORMERRORS).json()


    with transaction.atomic():
      
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

        
  try:
    epoxy.queryset(Document.objects.filter(corpus=c).prefetch_related('tags'))
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
        # print t
        tagsform = TagsForm({'type':t['type'], 'tags': ' '.join(t['tags'])})
      #tagsform = TagsForm()
        if not tagsform.is_valid():
          return epoxy.throw_error(error=tagsform.errors, code=API_EXCEPTION_FORMERRORS).json()
        epoxy.meta('tags', candidates_tags)

      with transaction.atomic():
        tags = []
        if candidates_tags:
          for candidate_type in candidates_tags:
            for tag in candidate_type['tags']:
              t, created = Tag.objects.get_or_create(type=candidate_type['type'], name=tag[:128])
              tags.append(t)
        #save documents and attach tags
        d.tags.add(*tags)
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
  # aniotate its text...
  epoxy.add('annotated', d.annotate())
  epoxy.add('text', d.text())

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

  # segments = Segment.objects.raw("""
  #   SELECT 
  #     s.`id`, s.`content`,s.`language`, 
  #     s.`cluster`, s.`status`, 
  #     MAX( ds.`tfidf`) AS `tfidf`,
  #     MAX( ds.`tf`) AS `tf`,
  #     COUNT( DISTINCT ds.document_id) AS `distribution` 
  #   FROM sven_segment s
  #     JOIN sven_document_segment ds ON s.id = ds.segment_id 
  #     JOIN sven_document d ON ds.document_id = d.id
  #   WHERE d.id = %(document_id)s
  #   GROUP BY s.cluster
  #   ORDER BY %(order_by)s
  #   LIMIT %(offset)s, %(limit)s
  #   """ % {
  #     'document_id': d.id,
  #     'order_by': ','.join(epoxy.order_by),
  #     'offset': epoxy.offset,
  #     'limit': epoxy.limit
  # })

  # epoxy.add('objects', [{
  #   'id': s.id,
  #   'tf': s.tf,
  #   'tf_idf': s.tfidf,
  #   'status': s.status,
  #   'cluster': s.cluster,
  #   'distribution': s.distribution,
  #   'content': s.content
  # } for s in segments])

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

  d = Document(corpus=corpus, raw=f, name=f.name.encode('utf8'), abstract=Document.DOCUMENT_ABSTRACT_PLACEHOLDER)
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
  '''
  Rest API for sven.models.Corpus
  On Post (authentified) request, it create a corpus
  only if the number of corpora is less than the declared settings.MAX_CORPORA_PER_USER
  '''
  epoxy = Epoxy(request)

  if not request.user.is_staff:
    if request.user.corpora.count() >= settings.MAX_CORPORA_PER_USER:
      return epoxy.throw_error(error="You have reached the maximum number of corpus available. Not staff user cannot have more than %s corpora" % settings.MAX_CORPORA_PER_USER, code=API_EXCEPTION_AUTH).json()
  
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
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  # translate epoxy filters: prepend document__ to every fields.
  cluster_filters = {}
  tags_filters = {}

  for key,value in epoxy.filters.iteritems():
    if key.startswith('tags__'):
      cluster_filters['document__%s' % key] = value
      tags_filters[ key.replace('tags__', '')] = value
    elif key.startswith('segments__'):
      cluster_filters[key.replace('segments__', 'document__segments__')] = value
    else:
      cluster_filters['document__%s' % key] = value

  grouping = {}

  # available data grouping (translations for MYSQL)
  DATE_GROUPING = {
    'Y': "%%Y",
    'Ym' : "%%Y-%%m",
    'Ymd' : "%%Y-%%m-%%d"
  }

  if 'group_by' in epoxy.data and not epoxy.data['group_by'] in DATE_GROUPING.keys():
    availablegrouping = Tag.objects.filter(tagdocuments__corpus=cor).values('type')
    epoxy.meta('q', any(epoxy.data['group_by'] in t['type'] for t in availablegrouping))
    grouping['document__tags__type'] = epoxy.data['group_by']
  

  # get cluster belonging to the correct grouping...
  clusters = Document_Segment.objects.filter(**grouping).filter(document__corpus=cor, segment__status=Segment.IN).filter(**cluster_filters).order_by(*epoxy.order_by).values('segment__cluster').annotate(
    distribution=Count('document', distinct=True),
    tf=Max('tf'),
    tfidf=Max('tfidf'),
    contents = GroupConcat('segment__content', separator='||'),
  )

  clusters_objects = []
  
  
  if 'group_by' in epoxy.data:
    groups_available = None
    
    
    epoxy.meta('grouping', epoxy.data['group_by']) 

    if epoxy.data['group_by'] in DATE_GROUPING.keys():
      #get only clusters related to a dated document...
      clusters = clusters.exclude(document__date__isnull=True)
      clusters_objects = [c for c in clusters[epoxy.offset : epoxy.offset + epoxy.limit]]
  
      # get all groupin possibilities according to date:
      groups_available = Document.objects.filter(corpus=cor).extra(
        select={'G': """DATE_FORMAT(date, "%s")""" % DATE_GROUPING[epoxy.data['group_by']]}
      ).values('G').annotate(distribution=Count('id'))
      
      # get groupings e.g value for groups for selected cluster only
      groups = Document_Segment.objects.exclude(document__date__isnull=True).filter(
        document__corpus=cor,
        segment__status='IN'
      ).filter(**epoxy.filters).filter(segment__cluster__in=[c['segment__cluster'] for c in clusters_objects]).extra(
        select={'G': """DATE_FORMAT(date, "%s")"""% DATE_GROUPING[epoxy.data['group_by']]}
      ).order_by().values('G', 'segment__cluster').annotate(
        distribution=Count('document', distinct=True),
        tf=Max('tf'),
        tfidf=Max('tfidf')
      )

    elif any(epoxy.data['group_by'] in t['type'] for t in availablegrouping):
      # get only clusters related to a dated document...
      clusters = clusters.filter(document__tags__type=epoxy.data['group_by'])
      clusters_objects = [c for c in clusters[epoxy.offset : epoxy.offset + epoxy.limit]]
  
      # get all groupin possibilities according to the selected tag type:
      groups_available = Tag.objects.filter(
        tagdocuments__corpus=cor,
        type=epoxy.data['group_by']
      ).filter(**tags_filters).prefetch_related('tagdocuments').distinct().values('name', 'id', 'slug').annotate(
        distribution=Count('tagdocuments')
      )
      
      groups = Document_Segment.objects.filter(
        document__corpus=cor,
        segment__status=Segment.IN,
        document__tags__type=epoxy.data['group_by']
      ).filter(**cluster_filters).filter(segment__cluster__in=[c['segment__cluster'] for c in clusters_objects]).extra(
        select={'G':'sven_tag.name'}).order_by().values('G', 'segment__cluster').annotate(
        distribution=Count('document', distinct=True),
        tf=Max('tf'),
        tfidf=Max('tfidf')
      )

    if groups_available is not None:
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

  else:
    clusters_objects = [c for c in clusters[epoxy.offset : epoxy.offset + epoxy.limit]]

  #outputting values
  epoxy.add('objects', clusters_objects)
  # get global min and global max for clusters
  epoxy.meta('bounds', Document_Segment.objects.filter(document__corpus=cor, segment__status='IN').aggregate(max_tf=Max('tf'), min_tf=Min('tf'), max_tfidf=Max('tfidf'), min_tfidf=Min('tfidf')))
  # get total number of clusters
  epoxy.meta('total_count', clusters.count())
  
  return epoxy.json()




def export_corpus_concepts(request, corpus_pk):
  '''
  Export filtered segments for q specified corpus
  Given by filters params as JSON - as usual, Filters need to be prefixed either with document__ or segment__ prefixes
  '''
  epoxy = Epoxy(request)
  try:
    cor = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  # translate epoxy filters: prepend document__ to every fields.
  cluster_filters = {}
  tags_filters = {}

  for key,value in epoxy.filters.iteritems():
    if key.startswith('tags__'):
      cluster_filters['document__%s' % key] = value
      tags_filters[ key.replace('tags__', '')] = value
    elif key.startswith('segments__'):
      cluster_filters[key.replace('segments__', 'document__segments__')] = value
    else:
      cluster_filters['document__%s' % key] = value

  import unicodecsv
  from django.http import HttpResponse
  
  if 'plain-text' not in epoxy.data:
    response = HttpResponse(content_type='text/csv')
    response['Content-Description'] = "File Transfer";
    response['Content-Disposition'] = "attachment; filename=%s.concepts.csv" % cor.name 
  
  else:

    response = HttpResponse(content_type='text/plain; charset=utf-8')

  
    

  clusters = Document_Segment.objects.filter(document__corpus=cor, segment__status=Segment.IN).filter(**cluster_filters).order_by(*epoxy.order_by).values('segment__cluster').annotate(
    distribution=Count('document', distinct=True),
    contents = GroupConcat('segment__content', separator='||'),
    tf=Max('tf'),
    tfidf=Max('tfidf')
  )

  
  clusters_objects = []
  groups_available = None
  if not 'group_by' in epoxy.data:
    print clusters.count()
    clusters_objects = [c for c in clusters]
  else:
    # available data grouping (translations for MYSQL)
    
    epoxy.meta('grouping', epoxy.data['group_by']) 


    if epoxy.data['group_by'] in DATE_GROUPING.keys():
      #get only clusters related to a dated document...
      clusters = clusters.exclude(document__date__isnull=True)
      print epoxy.offset, epoxy.limit
      clusters_objects = [c for c in clusters[epoxy.offset : epoxy.offset + 1000]]
  
      # get all groupin possibilities according to date:
      groups_available = Document.objects.filter(corpus=cor).extra(
        select={'G': """DATE_FORMAT(date, "%s")""" % DATE_GROUPING[epoxy.data['group_by']]}
      ).values('G').annotate(distribution=Count('id'))
      
      # get groupings e.g value for groups for selected cluster only
      groups = Document_Segment.objects.filter(
        document__corpus=cor,
        segment__status='IN'
      ).filter(segment__cluster__in=[c['segment__cluster'] for c in clusters_objects]).extra(
        select={'G': """DATE_FORMAT(date, "%s")"""% DATE_GROUPING[epoxy.data['group_by']]}
      ).order_by().values('G', 'segment__cluster').annotate(
        distribution=Count('document', distinct=True),
        tf=Max('tf'),
        tfidf=Max('tfidf')
      )

    elif any(epoxy.data['group_by'] in t for t in Tag.TYPE_CHOICES):
      # get only clusters related to a dated document...
      clusters = clusters.filter(document__tags__type=epoxy.data['group_by'])
      clusters_objects = [c for c in clusters[epoxy.offset : epoxy.offset + epoxy.offset + 1000]]
  
      # get all groupin possibilities according to the selected tag type:
      groups_available = Tag.objects.filter(
        tagdocuments__corpus=cor,
        type=epoxy.data['group_by']
      ).filter(**tags_filters).prefetch_related('tagdocuments').distinct().extra(
        select={'G': 'sven_tag.name'}
      ).values('G', 'name', 'id', 'slug').annotate(
        distribution=Count('tagdocuments')
      )
      
      groups = Document_Segment.objects.filter(
        document__corpus=cor,
        segment__status=Segment.IN,
        document__tags__type=epoxy.data['group_by']
      ).filter(**cluster_filters).filter(segment__cluster__in=[c['segment__cluster'] for c in clusters_objects]).extra(
        select={'G':'sven_tag.name'}).order_by().values('G', 'segment__cluster').annotate(
        distribution=Count('document', distinct=True),
        tf=Max('tf'),
        tfidf=Max('tfidf')
      )
    else:
      epoxy.warning('grouping', 'grouping not recognized, should be one value among these (for tags): %s' % ','.join([t[0] for t in Tag.TYPE_CHOICES])) 
      return epoxy.json()
    
  if groups_available is not None:
    groups_available = groups_available[0:100]
    print groups_available
    fieldnames = [
      'segment__cluster',
      'contents',
      'cluster',
      'tfidf', 
      'tf', 
      'distribution',
      'exclude'
    ] + sorted(set(['%s_tfidf' % g['G'] for g in groups_available] + ['%s_tf' % g['G'] for g in groups_available]))
  else:
    fieldnames = [
      'segment__cluster',
      'contents',
      'cluster',
      'tfidf', 
      'tf', 
      'distribution',
      'exclude'
    ]
  writer = unicodecsv.DictWriter(response, fieldnames=fieldnames, delimiter=',', encoding='utf-8')
  writer.writeheader()
    
  # find the right  matching the group name
  for cluster in clusters_objects:
    cluster['cluster'] = cluster['segment__cluster'];
    cluster['exclude'] = '';
    if groups_available is not None:
      for g in groups:
        if g['segment__cluster'] == cluster['segment__cluster']:
          cluster['%s_tfidf' % g['G']] = g['tfidf']
          cluster['%s_tf' % g['G']] = g['tf']
                  

  for cluster in clusters_objects:
    writer.writerow(cluster)




    

      #epoxy.add('groups', [g.json() for g in set([g['G'] for g in groups])])
  

  
  return response  
  #outputting values
  # epoxy.add('objects', clusters_objects)
  # # get global min and global max for clusters
  # epoxy.meta('bounds', Document_Segment.objects.filter(document__corpus=cor, segment__status='IN').aggregate(max_tf=Max('tf'), min_tf=Min('tf'), max_tfidf=Max('tfidf'), min_tfidf=Min('tfidf')))
  # # get total number of clusters
  # epoxy.meta('total_count', clusters.count())
  
  # return epoxy.json()


def stream_corpus_concepts(request, corpus_pk):
  '''
  draw stream (based on group stress.)
  '''
  epoxy = Epoxy(request)
  #remap filters
  filters = {}
  for key,value in epoxy.filters.iteritems():
    if key.startswith('tags__'):
      filters['document__%s' % key] = value
    elif key.startswith('segments__'):
      filters[key.replace('segments__', 'document__segments__')] = value
    else:
      filters['document__%s' % key] = value

  date_format = """strftime("%s", date)""" % '%Y-%m' if settings.DATABASES['default']['ENGINE'].endswith("sqlite3") else """DATE_FORMAT(date, "%s")""" % DATE_GROUPING['Ymd']
  # get group availability with current filters.
  groups_available = Document.objects.exclude(date__isnull=True).filter(corpus__pk=corpus_pk).filter(**epoxy.filters).extra(
        select={'G': date_format } # sqlite users strftime('%m-%Y',pubdate)
      ).values('G').annotate(distribution=Count('id'),date=Max('date'))
  
  print filters  
  #get number of groups

  for g in groups_available:

    # for each group, get the list of top concept according to the current orderby.
    groups = Document_Segment.objects.filter(
      document__date=g['date'],
      document__corpus__pk=corpus_pk,
      segment__status='IN'
    ).filter(
      **filters
    ).extra(
      select={'G': date_format}
    ).order_by(
      '-tf'
    ).values('G', 'segment__cluster').annotate(
      distribution=Count('document', distinct=True),
      contents = GroupConcat('segment__content', separator='||'),
      tf=Max('tf'),
      tfidf=Max('tfidf')
    )[:epoxy.limit]

    g['values'] = [d for d in groups]

  epoxy.add('objects', [g for g in groups_available])
  return epoxy.json()



def network_corpus(request, corpus_pk, model):
  '''

  '''
  

  epoxy = Epoxy(request)

  BIPARTITE_SET = 1 if model == 'concept' else 0

  #remap filters
  filters = {}
  for key,value in epoxy.filters.iteritems():
    if key.startswith('tags__'):
      filters['document__%s' % key] = value
    elif key.startswith('segments__'):
      filters[key.replace('segments__', 'document__segments__')] = value
    else:
      filters['document__%s' % key] = value


  #  get the list of concepts along with their connections
  segments = Document_Segment.objects.filter(
    document__corpus__pk=corpus_pk,
    segment__status='IN'
  ).filter(
    **filters
  ).values(
    'segment__cluster',
    'segment__content',
    'document__pk',
    'document__name',
    'tf',
    'tfidf'
  ).order_by('-tf')[:1000]

  G = nx.Graph()

  clusters = {}
  edges    = {}

  for s in segments:
    source = s['segment__cluster']
    target = s['document__pk']

    G.add_node(target, bipartite=0)
    G.add_node(source, bipartite=1)

    if BIPARTITE_SET == 1:
      G.node[source]['name']     = s['segment__content']
      G.node[source]['type']     = 'segments__cluster'
      G.node[source]['cluster'] = s['segment__cluster']
      G.node[source]['tf']       = max(0, s['tf'])
      G.node[source]['tfidf']    = max(0, s['tfidf'])
    else :
      G.node[target]['name'] = s['document__name']
      G.node[target]['type'] = 'document'

    if G.has_edge(source, target):
      G[source][target]['weight'] += 1
    else: # new edge. add with weight=1
      G.add_edge(source, target, weight=1)

  segments = [];

  
  # bottom_nodes, top_nodes = bipartite.sets(G)
  top_nodes = set(n for n,d in G.nodes(data=True) if d['bipartite']== BIPARTITE_SET)
  G1 = bipartite.generic_weighted_projected_graph(G, top_nodes, weight_function=jaccard)

  #   if s['segment__cluster'] not in clusters:
  #     clusters[s['segment__cluster']] = []
  #   clusters[s['segment__cluster']].append(s)

  # # clean segments
  # segments = [];

  # # get edge index
  # for k, collection in clusters.iteritems():
  #   for cluster in collection:
  epoxy.meta('total_count', {
    'nodes': G1.number_of_nodes(),
    'edges': G1.number_of_edges()
  })
  j = json_graph.node_link_data (G1)
  epoxy.add('edges', j['links'])
  epoxy.add('nodes', j['nodes'])

  # calculate cooccurrences


  return epoxy.json()



def network_corpus_tag(request, corpus_pk):
  # as network_corpus, but tag to tag jaccard similarity
  # with filters
  epoxy = Epoxy(request)
  
  fragments = Document.objects.filter(
    corpus__pk=corpus_pk
  ).filter(
    **epoxy.filters
  ).values(
    'tags__slug',
    'tags__name',
    'pk',
    'name'
  )

  G = nx.Graph()

  clusters = {}
  edges    = {}

  for s in fragments:
    if s['tags__slug'] is None:
      continue
    source = s['pk']
    target = s['tags__slug']

    G.add_node(target, bipartite=0)
    G.add_node(source, bipartite=1)

    G.node[source]['name'] = s['name']
    G.node[source]['type'] = 'document'
    G.node[target]['type'] = 'tags__slug'
    G.node[target]['name'] = s['tags__name']
    G.node[target]['f'] = G.node[target]['f']+1 if 'f' in G.node[target] else 1
    G.node[target]['tf'] = math.sqrt(G.node[target]['f']) * 2

    if G.has_edge(source, target):
      G[source][target]['weight'] += 1
    else: # new edge. add with weight=1
      G.add_edge(source, target, weight=1)

  fragments = [];

  
  # bottom_nodes, top_nodes = bipartite.sets(G)
  top_nodes = set(n for n,d in G.nodes(data=True) if d['bipartite']== 0)
  G1 = bipartite.generic_weighted_projected_graph(G, top_nodes, weight_function=jaccard)

  epoxy.meta('total_count', {
    
  })
  j = json_graph.node_link_data (G1)
  epoxy.add('edges', j['links'])
  epoxy.add('nodes', j['nodes'])
  return epoxy.json()



def import_corpus_concepts(request, corpus_pk):
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
      filepath = c.saveCSV(request.FILES['file'], prefix='concepts')
      # launch command
      job = Job.start(corpus=c, command='importconcepts', csv=filepath)
      if job is not None:
        epoxy.item(job)
      else:
        return epoxy.throw_error(error='a job is already running', code='BUSY').json()
    else:
      return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()
  else:
    pass  
  return epoxy.json()


def __export_corpus_concepts(request, corpus_pk):
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
  
  if 'plain-text' not in epoxy.data:
    response = HttpResponse(mimetype='text/csv; charset=utf-8')
    response['Content-Description'] = "File Transfer";
    response['Content-Disposition'] = "attachment; filename=%s.concepts.csv" % cor.name 
  
  else:

    response = HttpResponse(content_type='text/plain; charset=utf-8')
  
  fieldnames = clusters[0].keys() + ['content', 'status', 'ordering']
  DATE_GROUPING = {
    'Ym' : "%%Y-%%m",
    'Ymd' : "%%Y-%%m-%%d"
  }
  if 'group_by' in epoxy.data:
    if epoxy.data['group_by'] in DATE_GROUPING.keys():
      # available data grouping (translations for MYSQL ONLY !)
      groups_available = Document.objects.filter(corpus=cor).extra(
        select={'G': """DATE_FORMAT(date, "%s")""" % DATE_GROUPING[epoxy.data['group_by']]}
      ).values('G').annotate(distribution=Count('id'))
      for g in groups_available:
        fieldnames = fieldnames + [
          '%s (tf)' % g['G'],
          '%s (tfidf)' % g['G']
        ]
    elif any(epoxy.data['group_by'] in t for t in Tag.TYPE_CHOICES):
      # get all groupin possibilities according to date:
      groups_available = Tag.objects.filter(
        tagdocuments__corpus=cor
      ).filter(**tags_filters).prefetch_related('tagdocuments').distinct().values('name', 'id', 'slug').annotate(
        distribution=Count('tagdocuments')
      )
      for g in groups_available:
        fieldnames = fieldnames + [
          '%s (tf)' % g['name'],
          '%s (tfidf)' % g['name']
        ]


  
  writer = unicodecsv.DictWriter(response, fieldnames=fieldnames, delimiter=',', encoding='utf-8')
  writer.writeheader()


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

    groups=None
    # get group values for the indexed clusters only
    if 'group_by' in epoxy.data:
      if epoxy.data['group_by'] in DATE_GROUPING.keys():
        groups = Document_Segment.objects.filter(
          document__corpus=cor,
          segment__status='IN'
        ).filter(**epoxy.filters).filter(segment__cluster__in=clusterindex.keys()).extra(
          select={'G': """DATE_FORMAT(date, "%%Y-%%m")"""}
        ).order_by().values('G', 'segment__cluster').annotate(
          distribution=Count('document', distinct=True),
          tf=Max('tf'),
          tf_idf=Max('tfidf')
        )

        
      elif any(epoxy.data['group_by'] in t for t in Tag.TYPE_CHOICES):
        groups = Document_Segment.objects.filter(
          document__corpus=cor,
          segment__status=Segment.IN,
          document__tags__type=epoxy.data['group_by']
        ).filter(**epoxy.filters).filter(segment__cluster__in=clusterindex.keys()).extra(
          select={'G':'sven_tag.name'}).order_by().values('G', 'segment__cluster').annotate(
          distribution=Count('document', distinct=True),
          tf=Max('tf'),
          tf_idf=Max('tfidf')
        )

      if 'group_by' in epoxy.data and groups:
        for c in clusterindex.values():
          for g in groups:
            if g['segment__cluster'] == c['segment__cluster']:
              c.update({
                '%s (tf)' % g['G']:  g['tf'],
                '%s (tfidf)' % g['G']:  g['tf_idf']
              })

    # get distinct segments matching the indexed clusters
    segments = Segment.objects.filter(cluster__in=clusterindex.keys()).order_by('cluster')
    
    # print lines
    pc = False# previouscluster
    for s in segments:
      if pc and pc == s.cluster:
        continue
      pc = s.cluster
      if s.cluster in clusterindex:
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
    response = HttpResponse(content_type='text/csv')
    response['Content-Description'] = "File Transfer";
    response['Content-Disposition'] = "attachment; filename=%s.documents.csv" % c.name 
  
  else:
    response = HttpResponse(content_type='text/plain; charset=utf-8')
  
  docs = Document.objects.filter(corpus=c).filter(**epoxy.filters)
  writer = unicodecsv.writer(response, delimiter=';', encoding='utf-8')
  categories = Tag.objects.filter(tagdocuments__corpus=c).values('type').annotate(c=Count('tagdocuments'))
  # write headers
  headers = [
    u'key',
    u'slug',
    u'mimetype',
    u'name',
    u'abstract',
    u'language',
    u'date',
    u'start_date',
    u'end_date',
    u'url',
    u'url_en',
  ]+  [t['type'] for t in categories] #[u'%s' % label for t,label in Tag.TYPE_CHOICES]
  
  writer.writerow(headers)
  
  for doc in docs:
    tags = {u'%s' % t['type']:[] for t in categories}
  
    for tag in doc.tags.all():
      if u'%s' % tag.type in tags:
        tags[u'%s' % tag.type].append(tag.name)

    row = [
      doc.id,
      doc.slug,
      doc.mimetype,
      doc.name,
      re.sub(r'[\n\r]', ' ', doc.abstract),
      doc.language,
      doc.date.strftime('%Y-%m-%d') if doc.date is not None else doc.date_created.strftime('%Y-%m-%d'),
      doc.date.strftime('%Y-%m-%d') if doc.date is not None else doc.date_created.strftime('%Y-%m-%d'),
      doc.date.strftime('%Y-%m-%d') if doc.date is not None else doc.date_created.strftime('%Y-%m-%d'),
      doc.url,
      os.path.join(doc.corpus.slug, os.path.basename(doc.raw.url)) if doc.raw else  os.path.join(doc.corpus.slug, doc.slug),
    ]

    for category in categories:
      row.append(u','.join(tags[category['type']])) # comma separated

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
  filters = {
    'timeline': [],
    'tags': {}
  }

  try:
    c = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST)

  ids = []
  docs = helper_get_available_documents(request=request, corpus=c).filter(**epoxy.filters)
  
  # deal with reduce and search field
  if epoxy.reduce:
    for r in epoxy.reduce:
      docs = queryset.filter(r)

  if epoxy.search:
    docs = queryset.filter( Document.search(epoxy.search)).distinct()

  for d in docs:
    ids.append(d.id)

  # get dates.
  for t in docs.exclude(date__isnull=True).order_by().extra(select={'day': 'date( date )'}).values('day').annotate(count=Count('id')):
    filters['timeline'].append(t)
  


  epoxy.meta('filtered_count', len(ids))
  
  for chunk_ids in helper_chunk_list(ids, 50):
    
    for t in Tag.objects.filter(tagdocuments__id__in=chunk_ids):
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
  cursor = connection.cursor()
  cursor.execute("""
    SELECT t1.name as source, t2.name as target, t1.id as source_id, t2.id as target_id, COUNT(DISTINCT td1.document_id) as weight
      FROM 
        sven_tag t1
          JOIN sven_document_tags td1
            ON t1.id = td1.tag_id
          JOIN sven_document d1
            ON d1.id = td1.document_id,
        sven_tag t2
          JOIN sven_document_tags td2
            ON t2.id = td2.tag_id
          JOIN sven_document d2
            ON d2.id = td2.document_id
    WHERE d1.corpus_id = %(corpus_pk)s
      AND d2.corpus_id = %(corpus_pk)s 
      AND t1.id != t2.id
      AND td1.document_id = td2.document_id
    GROUP BY source, target
    ORDER BY weight DESC
    LIMIT 500
  """ % {
    'corpus_pk': corpus_pk
  })
  
  edges = {}
  nodes = {}
  for row in cursor:
    # our graph node id
    edge_id = '.'.join(sorted([str(row[2]), str(row[3])]))
    if edge_id in edges:
      continue
    nodes[int(row[2])] = {
      'id': int(row[2]),
      'name': row[0]
    }
    nodes[int(row[3])] = {
      'id': int(row[3]),
      'name': row[1]
    }
    edges[edge_id] = {
      'id':      edge_id,
      'source':  int(row[2]),
      'target':  int(row[3]),
      'weight':  int(row[4])
    }  
  
  epoxy.add('nodes', nodes.values())
  epoxy.add('edges', edges.values())
  
  return epoxy.json()


@login_required(login_url='/api/login')
def graph_corpus_concepts(request, corpus_pk):
  '''
  corpus tags as nodes-edges value
  '''
  epoxy = Epoxy(request)
  cursor = connection.cursor()
  cursor.execute("""
    SELECT s1.cluster, s2.cluster, COUNT(*) AS w
      FROM sven_document_segment t1
      INNER JOIN sven_document_segment t2 
      ON (t1.document_id=t2.document_id AND t1.segment_id<t2.segment_id)
      INNER JOIN sven_segment s1 ON t1.segment_id = s1.id 
      INNER JOIN sven_segment s2 ON t2.segment_id = s2.id
      GROUP BY s1.cluster,
      s2.cluster
      ORDER BY w DESC LIMIT 100
  """ % {
    'corpus_pk': corpus_pk
  })
  
  edges = {}
  nodes = {}
  for row in cursor:
    # our graph node id
    edge_id = '.'.join(sorted([row[0], row[1]]))
    if edge_id in edges:
      continue
    nodes[row[0]] = {
      'id': row[0],
      'name': row[0]
    }
    nodes[row[0]] = {
      'id': row[1],
      'name': row[1]
    }
    edges[edge_id] = {
      'id':      edge_id,
      'source':  row[0],
      'target':  row[1],
      'weight':  int(row[2])
    }  
  
  epoxy.add('nodes', nodes.values())
  epoxy.add('edges', edges.values())
  
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