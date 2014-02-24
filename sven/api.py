from django.db.models import Q
from sven.models import Corpus
from glue import Epoxy, API_EXCEPTION_AUTH, API_EXCEPTION_FORMERRORS, API_EXCEPTION_DOESNOTEXIST
from glue.api import edit_object



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
  result.throw_error(code=API_EXCEPTION_DOESNOTEXIST)
  return result.json()



def corpora(request):
  result = Epoxy(request)
  result.queryset(Corpus.objects.filter())
  return result.json()



def corpus(request):
  result = Epoxy(request)
  result.queryset(Corpus.objects.filter())
  return result.json()