from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin

import glue.urls
import twit.urls



admin.autodiscover()

apipatterns = patterns('sven.api',
  url(r'^$', 'home', name='sven_api_home'),
  url(r'^corpus$', 'corpora', name='sven_api_corpora'),
  url(r'^corpus/(?P<pk>\d+)$', 'corpus', name='sven_api_corpus'),
  url(r'^corpus/(?P<corpus_pk>\d+)/document$', 'corpus_documents', name='sven_api_corpus_documents'), # document per corpus
  url(r'^corpus/(?P<corpus_pk>\d+)/upload$', 'document_upload', name='sven_api_document_upload'),
  url(r'^corpus/(?P<corpus_pk>\d+)/start/(?P<cmd>[a-z\d]+)$', 'start', name='sven_api_start'),  # execute a job like management/start.py
  url(r'^corpus/(?P<corpus_pk>\d+)/segment$', 'corpus_segments', name='sven_api_corpus_segments'),
  url(r'^corpus/(?P<corpus_pk>\d+)/segment/(?P<segment_pk>\d+)$', 'corpus_segment', name='sven_api_corpus_segment'), #view modify segment cluster according to the current corpus
  
  url(r'^corpus/(?P<corpus_pk>\d+)/filters$', 'corpus_filters', name='sven_api_corpus_filters'), #view modify segment cluster according to the current corpus
  url(r'^corpus/(?P<corpus_pk>\d+)/stopwords$', 'corpus_stopwords', name='sven_api_corpus_stopwords'), #view modify segment cluster according to the current corpus
  
  url(r'^corpus/(?P<corpus_pk>\d+)/concept$', 'corpus_concepts', name='sven_api_corpus_concepts'), #view modify segment cluster according to the current corpus
  url(r'^corpus/(?P<corpus_pk>\d+)/related/tag$', 'corpus_tags', name='sven_api_corpus_tags'),

  url(r'^job$', 'jobs', name='sven_api_jobs'), #view modify segment cluster according to the current corpus
  url(r'^job/(?P<pk>\d+)$', 'job', name='sven_api_job'), #view modify segment cluster according to the current corpus
       
  # all availabe documents (per user)
  url(r'^document$', 'documents', name='sven_api_documents'), # user document 
  url(r'^document/(?P<pk>\d+)$', 'document', name='sven_api_document'), # user document (user must have access, or a nOT found error is thrown)
  url(r'^document/(?P<pk>\d+)/segments$', 'document_segments', name='sven_api_document_segments'), # get requet.user's document segments list (with simple tf idf)
  url(r'^document/(?P<pk>\d+)/tag$', 'document_tags', name='sven_api_document_tags'), # attach/detach a tag
  url(r'^document/(?P<pk>\d+)/upload$', 'document_text_version_upload', name='sven_api_document_upload_text'), # user document (user must have access, or a nOT found error is thrown)
  url(r'^document/(?P<pk>\d+)/download$', 'document_text_version_download', name='sven_api_document_download_text'), # user document (user must have access, or a nOT found error is thrown)
  
  # url(r'^document/(?P<pk>\d+)/tag/(?P<tag_pk>\d+)$', 'document_tag', name='sven_api_document_tag'), # delete document tag relationship. Return Document
  
  url(r'^tag$', 'tags', name='sven_api_tags'), # user document (user must have access, or a nOT found error is thrown)
    

  url(r'^profile$', 'profile', name='sven_api_profile'), # just single profile for security sake!
  url(r'^profile/(?P<pk>\d+)$', 'profile', name='sven_api_staff_profile'), # just single profile for security sake!
  
  url(r'^notification$', 'notification', name='sven_api_notification'),

  # export csv and gexfs files
  url(r'^export/corpus/(?P<corpus_pk>\d+)/document$', 'export_corpus_documents', name='sven_api_export_corpus_documents'),  # execute a job like management/start.py
  url(r'^export/corpus/(?P<corpus_pk>\d+)/segments$', 'export_corpus_segments', name='sven_api_export_corpus_segments'),  # execute a job like management/start.py
  url(r'^export/corpus/(?P<corpus_pk>\d+)/concepts$', 'export_corpus_concepts', name='sven_api_export_corpus_concepts'),  # execute a job like management/start.py
  
  url(r'^import/corpus/(?P<corpus_pk>\d+)/concepts$', 'import_corpus_concepts', name='sven_api_import_corpus_concepts'),  # execute the job importconcept management/start.py
  url(r'^import/corpus/(?P<corpus_pk>\d+)/document$', 'import_corpus_documents', name='sven_api_import_corpus_documents'),  # execute the job importtags management/start.py
  

  url(r'^d3/timeline$', 'd3_timeline', name='sven_api_d3_timeline'), # all user corpus timeline. restrict via filters
  url(r'^graph/corpus/(?P<corpus_pk>\d+)/tags$', 'graph_corpus_tags', name='sven_api_graph_corpus_tags'),
  url(r'^graph/corpus/(?P<corpus_pk>\d+)/concept$', 'graph_corpus_concepts', name='sven_api_graph_corpus_concepts'),
  url(r'^stream/corpus/(?P<corpus_pk>\d+)/concept$', 'stream_corpus_concepts', name='sven_api_stream_corpus_concepts'),
  url(r'^network/corpus/(?P<corpus_pk>\d+)/(?P<model>concept|document)$', 'network_corpus', name='sven_api_network_corpus'),
  url(r'^network/corpus/(?P<corpus_pk>\d+)/tag$', 'network_corpus_tag', name='sven_api_network_corpus_tag'),

  url(r'^login', 'require_login', name='sven_api_require_login'),
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
    url(r'^twit/', include(twit.urls)),

)

if settings.DEBUG:
  urlpatterns += patterns('django.views.static',
    (r'media/(?P<path>.*)', 'serve', {'document_root': settings.MEDIA_ROOT}),
  )
