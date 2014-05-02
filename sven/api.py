import subprocess, logging
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count

from glue import Epoxy, API_EXCEPTION_AUTH, API_EXCEPTION_FORMERRORS, API_EXCEPTION_DOESNOTEXIST
from glue.api import edit_object

from sven.forms import CorpusForm, DocumentForm, CorpusSegmentForm
from sven.models import Corpus, Document, Profile, Job, Segment


logger = logging.getLogger("sven")

   

def home(request):
  '''
  Help or manual should be placed here
  '''
  result = Epoxy(request)
  return result.json()



def notification(request):
  '''
  Tail
  '''
  epoxy = Epoxy(request)

  try:
    epoxy.add('log', subprocess.check_output(["tail", settings.LOG_FILE], close_fds=True))
  except OSError, e:
    logger.exception(e)
    
  jobs = Job.objects.filter(corpus__in=request.user.corpora.all())
  epoxy.queryset(jobs)
  epoxy.add('datetime', datetime.now().isoformat())

  return epoxy.json()



def not_found(request):
  '''
  Help or manual should be placed here
  '''
  result = Epoxy(request)
  result.throw_error(error='function does not exist')
  return result.json()



@login_required
def start(request, corpus_pk, cmd):
  epoxy = Epoxy(request)

  try:
    c = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_DOESNOTEXIST).json()

  logger.debug('starting "%s" on corpus %s' % (cmd, corpus_pk))
    
  job = Job.start(corpus=c, command=cmd)
  if job is not None:
    epoxy.item(job)
  return epoxy.json()



@login_required
def documents(request, corpus_pk):
  epoxy = Epoxy(request)
  
  try:
    c = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  if epoxy.is_POST(): # add a new document and attach it to this specific corpus. Content would be attached later, via upload. @todo
    form = DocumentForm(request.REQUEST)
    if form.is_valid():
      d = form.save(commit=False)
      d.corpus = c
      d.save()
      epoxy.item(d, deep=False)
    else:
      return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()

  epoxy.queryset(Document.objects.filter(corpus=c))
  return epoxy.json()



@login_required
def document(request, pk):
  epoxy = Epoxy(request)
  
  try:
    d = Document.objects.get(pk=pk, corpus=request.user.corpora.all())
  except Document.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()
  
  epoxy.item(d, deep=True)

  return epoxy.json()



@login_required
def document_segments(request, pk):
  epoxy = Epoxy(request)
  try:
    d = Document.objects.get(pk=pk, corpus__owners=request.user)
  except Document.DoesNotExist, e:
    return result.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()
  
  segments = Segment.objects.raw("""
    SELECT 
      s.`id`, s.`content`,s.`language`, 
      s.`cluster`, s.`status`, 
      MAX( ds.`tfidf`) AS `max_tfidf`,
      MAX( ds.`tf`) AS `max_tf`,
      COUNT( DISTINCT ds.document_id) AS `num_clusters` 
    FROM sven_segment s
      JOIN sven_document_segment ds ON s.id = ds.segment_id 
      JOIN sven_document d ON ds.document_id = d.id
    WHERE d.id = %s
    GROUP BY s.cluster
    ORDER BY max_tf DESC
    """,[d.id]
  )

  epoxy.add('objects', [{
    'max_tf': s.max_tf,
    'status': s.status,
    'cluster': s.cluster,
    'num_clusters': s.num_clusters,
    'content': s.content
  } for s in segments])

  return epoxy.json()



@login_required
def document_upload(request, corpus_pk):
  try:
    corpus = Corpus.objects.get(pk=corpus_pk)
  except Corpus.DoesNotExist, e:
    return result.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  f = request.FILES['file']
  d = Document(corpus=corpus, raw=f, name=f.name)
  d.save()
  print d

  epoxy = Epoxy(request)
  return epoxy.json()



@login_required
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
  result = Epoxy(request)

  try:
    corpus = Corpus.objects.get(pk=pk)
  except Corpus.DoesNotExist, e:
    return result.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  if result.is_DELETE():
    corpus.delete()
  else:
    result.item(corpus, deep=True)

  return result.json()



@login_required
def corpus_segments(request, corpus_pk):
  '''
  Return the list of segments in a specific corpus (given by pk)
  '''
  epoxy = Epoxy(request)
  try:
    c = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return result.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()
  
  if not epoxy.order_by:
    epoxy.order_by = ['max_tf DESC']

  segments = Segment.objects.raw("""
    SELECT 
      s.`id`, s.`content`,s.`language`, 
      s.`cluster`, s.`status`, 
      MAX( ds.`tfidf`) AS `max_tfidf`,
      MAX( ds.`tf`) AS `max_tf`,
      COUNT(DISTINCT ds.document_id) AS `distribution` 
    FROM sven_segment s
      JOIN sven_document_segment ds ON s.id = ds.segment_id 
      JOIN sven_document d ON ds.document_id = d.id
      JOIN sven_corpus c ON d.corpus_id = c.id
    WHERE c.id = %s
    GROUP BY s.cluster
    ORDER BY distribution DESC, max_tf DESC
    LIMIT %s, %s
    """,[c.id,  epoxy.offset, epoxy.limit]
  )

  epoxy.add('objects', [{
    'id': s.id,
    'tf': s.max_tf,
    'status': s.status,
    'cluster': s.cluster,
    'distribution': s.distribution,
    'content': s.content
  } for s in segments])

  return epoxy.json()



@login_required
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
      #Segment.objects.filter(cluster=, documents)
      #form.cleaned_data['status'],form.cleaned_data['cluster']

      pass
    else:
      return epoxy.throw_error(error=form.errors,code=API_EXCEPTION_FORMERRORS).json()

  if not epoxy.order_by:
    epoxy.order_by = ['ds.`tf` DESC', 'ds.document_id DESC']

  segments = Segment.objects.raw("""
    SELECT 
      s.`id`, s.`content`,s.`language`, 
      s.`cluster`, ds.`status`, 
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



@login_required
def profile(request, pk=None):
  '''
  return authenticated user's profile.
  If user is staff he can see everything
  '''
  epoxy = Epoxy(request)

  try:
    pro = User.objects.get(pk=pk).profile if pk is not None and request.user.is_staff else request.user.profile
  except Profile.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  return epoxy.item(pro, deep=True).json()



@login_required
def corpus_filters(request, corpus_pk):
  '''
  return corpus documents timeline, tags distribution etc...
  If user is staff he can see everything
  '''
  epoxy = Epoxy(request)
  return epoxy.json()



@login_required
def download(request, corpus_pk):
  pass