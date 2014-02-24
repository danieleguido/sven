from django.contrib.auth.decorators import login_required
from django.db.models import Q

from glue import Epoxy, API_EXCEPTION_AUTH, API_EXCEPTION_FORMERRORS, API_EXCEPTION_DOESNOTEXIST
from glue.api import edit_object

from sven.forms import CorpusForm, DocumentForm
from sven.models import Corpus, Document



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



def corpora(request):
  result = Epoxy(request)

  if result.is_POST():
    form = CorpusForm(request.REQUEST)
    if form.is_valid():
      corpus = form.save(commit=False)
      corpus.save()
      corpus.owners.add(request.user)
      corpus.save()
      result.item(corpus)
    else:
      return result.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()

  result.queryset(Corpus.objects.filter(owners=request.user))
  return result.json()



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