# __init__.py
# common api endpoint or api enpoint not belonging to a specific model
from datetime import datetime
from sven.serializer import Glue
from sven.models import Corpus, Document, Tag
from corpus import items, item
from django.contrib.auth.decorators import login_required

def echo(request):
  '''
  Help or manual should be placed here
  '''
  result = Glue(request)
  return result.json()

@login_required(login_url='/api/login')
def notification(request):
  '''
  Tail
  '''
  epoxy = Glue(request)
  epoxy.meta('profile', request.user.profile.json())
    
  #try:
  #  epoxy.add('log', subprocess.check_output(["tail", settings.LOG_FILE], close_fds=True))
  #except OSError, e:
  #  logger.exception(e)
  # DEPRECATED. too much. 
  corpora = Corpus.objects.filter(owners=request.user)
  # jobs = Job.objects.filter(corpus__owners=request.user)
  # available tags. to be cached somehow
  tags = Tag.objects.filter(type=Tag.TYPE_OF_MEDIA)

  epoxy.queryset(corpora)
  # print [j.json() for j in corpora]

  # try:
  #   epoxy.add('jobs', [j.json() for j in jobs])
  # except Document.DoesNotExist, e:
  epoxy.add('jobs', [])

  epoxy.add('tags', [t.json() for t in tags])
  epoxy.add('datetime', datetime.now().isoformat())

  return epoxy.json()
