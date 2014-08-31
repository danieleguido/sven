from django.contrib.auth.decorators import login_required

from glue import Epoxy, API_EXCEPTION_AUTH, API_EXCEPTION_FORMERRORS, API_EXCEPTION_DOESNOTEXIST
from glue.api import edit_object

from twit.forms import AccountForm
from twit.models import Account

from sven.models import Corpus


def index(request):
  '''
  Help or manual should be placed here
  '''
  epoxy = Epoxy(request)
  return epoxy.json()



@login_required
def account(request, pk):
  epoxy = Epoxy(request)
  try:
    epoxy.item(Account.objects.get(pk=pk, corpora=request.user.corpora.all()))
  except Account.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()
  return epoxy.json()



@login_required
def accounts(request):
  epoxy = Epoxy(request)
  if epoxy.is_POST():
    form = AccountForm(epoxy.data)
    
    if not form.is_valid():
      return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()
    
    # check corpus id
    try:
      cor = Corpus.objects.get(pk=form.cleaned_data['corpus'], owners=request.user)
    except Corpus.DoesNotExist, e:
      return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()
  
    acc, created = Account.objects.get_or_create(url=form.cleaned_data['url'])
    acc.corpora.add(cor) # copy documents into corpus?
    acc.save()

  epoxy.queryset(Account.objects.filter(corpora=request.user.corpora.all()))
  return epoxy.json()
