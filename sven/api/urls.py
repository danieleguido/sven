from django.conf.urls import url

import sven.api

urlpatterns = [
  url(r'^$', sven.api.echo, name='sven_api_echo'),
  url(r'^notification$', sven.api.notification, name='sven_api_notification'),


  url(r'^corpus$', sven.api.corpus.items, name='sven_api_corpora'),
  url(r'^corpus/(?P<pk>\d+)$', sven.api.corpus.item, name='sven_api_corpus'),
]