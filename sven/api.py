from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from glue import Epoxy, API_EXCEPTION_AUTH, API_EXCEPTION_FORMERRORS, API_EXCEPTION_DOESNOTEXIST
from glue.api import edit_object

from sven.forms import CorpusForm, DocumentForm
from sven.models import Corpus, Document, Profile



def home(request):
  '''
  Help or manual should be placed here
  '''
  result = Epoxy(request)
  return result.json()



def not_found(request):
  '''
  Help or manual should be placed here
  '''
  result = Epoxy(request)
  result.throw_error(error='function does not exist')
  return result.json()


@login_required
def documents(request, corpus_pk):
  result = Epoxy(request)
  
  try:
    c = Corpus.objects.get(pk=corpus_pk, owners=request.user)
  except Corpus.DoesNotExist, e:
    return result.throw_error(error=form.errors, code=API_EXCEPTION_DOESNOTEXIST).json()

  if result.is_POST(): # add a new document and attach it to this specific corpus. Content would be attached later, via upload. @todo
    form = DocumentForm(request.REQUEST)
    if form.is_valid():
      d = form.save(commit=False)
      d.corpus = c
      d.save()
      result.item(d, deep=False)
    else:
      return result.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()

  result.queryset(Document.objects.filter(corpus=c))
  return result.json()



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
  