from django.conf.urls import patterns, url

urlpatterns = patterns('twit.api',
  url(r'^$', 'index'),
  url(r'account$', 'accounts'),
  url(r'account/(?P<pk>\d+)$', 'account'),
)
