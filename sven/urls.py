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

    url(r'^admin/', include(admin.site.urls)),
    url(r'^glue/', include(glue.urls)),
)