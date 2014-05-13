from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin

import glue.urls



admin.autodiscover()

apipatterns = patterns('sven.api',
  url(r'^$', 'home', name='sven_api_home'),
  url(r'^corpus$', 'corpora', name='sven_api_corpora'),
  url(r'^corpus/(?P<pk>\d+)$', 'corpus', name='sven_api_corpus'),
  url(r'^corpus/(?P<corpus_pk>\d+)/document$', 'documents', name='sven_api_documents'),
  url(r'^corpus/(?P<corpus_pk>\d+)/upload$', 'document_upload', name='sven_api_document_upload'),
  url(r'^corpus/(?P<corpus_pk>\d+)/start/(?P<cmd>[a-z\d]+)$', 'start', name='sven_api_start'),  # execute a job like management/start.py
  url(r'^corpus/(?P<corpus_pk>\d+)/segment$', 'corpus_segments', name='sven_api_corpus_segments'),
  url(r'^corpus/(?P<corpus_pk>\d+)/segment/(?P<segment_pk>\d+)$', 'corpus_segment', name='sven_api_corpus_segment'), #view modify segment cluster according to the current corpus
  
  url(r'^corpus/(?P<corpus_pk>\d+)/filters$', 'corpus_filters', name='sven_api_corpus_filters'), #view modify segment cluster according to the current corpus
  
  url(r'^job$', 'jobs', name='sven_api_jobs'), #view modify segment cluster according to the current corpus
  url(r'^job/(?P<pk>\d+)$', 'job', name='sven_api_job'), #view modify segment cluster according to the current corpus
       

  url(r'^document/(?P<pk>\d+)$', 'document', name='sven_api_document'), # user document (user must have access, or a nOT found error is thrown)
  url(r'^document/(?P<pk>\d+)/segments$', 'document_segments', name='sven_api_document_segments'), # get requet.user's document segments list (with simple tf idf)
    

  url(r'^profile$', 'profile', name='sven_api_profile'), # just single profile for security sake!
  url(r'^profile/(?P<pk>\d+)$', 'profile', name='sven_api_staff_profile'), # just single profile for security sake!
  
  url(r'^notification$', 'notification', name='sven_api_notification'),

  url(r'^.*$', 'not_found', name='sven_api_not_found'),
)

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'sven.views.home', name='sven_home'),
    url(r'^login/$', 'sven.views.login_view', name='sven_login'),
    url(r'^logout/$', 'sven.views.logout_view', name='sven_logout'),
    
    url(r'^api/', include(apipatterns)),
    
    
    # admin only
    url(r'^dev/$', 'sven.views.home_dev', name='sven_home_dev'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^glue/', include(glue.urls)),

)

if settings.DEBUG:
  urlpatterns += patterns('django.views.static',
    (r'media/(?P<path>.*)', 'serve', {'document_root': settings.MEDIA_ROOT}),
  )
