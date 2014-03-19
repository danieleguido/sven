import subprocess, logging
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count

from glue import Epoxy, API_EXCEPTION_AUTH, API_EXCEPTION_FORMERRORS, API_EXCEPTION_DOESNOTEXIST
from glue.api import edit_object

from sven.forms import CorpusForm, DocumentForm
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

  epoxy.add('log', subprocess.check_output(["tail", settings.LOG_FILE]))

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
    return result.throw_error(error=form.errors, code=API_EXCEPTION_DOESNOTEXIST).json()

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
    return epoxy.throw_error(error=e, code=API_EXCEPTION_DOESNOTEXIST).json()

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
    d = Document.objects.get(pk=pk, corpus__owners=request.user)
  except Document.DoesNotExist, e:
    return result.throw_error(error=e, code=API_EXCEPTION_DOESNOTEXIST).json()
  
  epoxy.item(d, deep=True)

  return epoxy.json()



@login_required
def document_segments(request, pk):
  epoxy = Epoxy(request)
  try:
    d = Document.objects.get(pk=pk, corpus__owners=request.user)
  except Document.DoesNotExist, e:
    return result.throw_error(error=e, code=API_EXCEPTION_DOESNOTEXIST).json()
  
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
def download(request, corpus_pk):
  pass