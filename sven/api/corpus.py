from sven.api import Glue
from sven.models import Corpus
from sven.forms import CorpusForm
from django.conf import settings
from django.contrib.auth.decorators import login_required

@login_required(login_url='/api/login')
def items(request):
  '''
  Rest API for sven.models.Corpus
  On Post (authentified) request, it create a corpus
  only if the number of corpora is less than the declared settings.MAX_CORPORA_PER_USER
  '''
  epoxy = Glue(request)

  if not request.user.is_staff:
    if hasattr(settings, 'MAX_CORPORA_PER_USER') and request.user.corpora.count() >= settings.MAX_CORPORA_PER_USER:
      return epoxy.throw_error(error="You have reached the maximum number of corpus available. Not staff user cannot have more than %s corpora" % settings.MAX_CORPORA_PER_USER, code=API_EXCEPTION_AUTH).json()
  
  if epoxy.is_POST():
    form = CorpusForm(epoxy.data)
    if form.is_valid():
      cor = form.save(commit=False)
      cor.save()
      cor.owners.add(request.user)
      cor.save()
      epoxy.item(cor)
    else:
      return epoxy.throw_error(error=form.errors, code=API_EXCEPTION_FORMERRORS).json()

  epoxy.queryset(Corpus.objects.filter(owners__in=[request.user]))
  return epoxy.json()



def item(request, pk):
  epoxy = Glue(request)

  try:
    cor = Corpus.objects.get(pk=pk)
  except Corpus.DoesNotExist, e:
    return epoxy.throw_error(error='%s'%e, code=API_EXCEPTION_DOESNOTEXIST).json()

  if epoxy.is_DELETE():
    cor.delete()
  else:
    epoxy.item(cor, deep=True)
    
  return epoxy.json()
