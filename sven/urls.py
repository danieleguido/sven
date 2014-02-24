from django.conf.urls import patterns, include, url

from django.contrib import admin

import glue.urls

admin.autodiscover()

apipatterns = patterns('sven.api',
  url(r'^$', 'home', name='sven_api_home'),
  url(r'^corpus/$', 'corpus', name='sven_api_corpora'),
  url(r'^corpus/(?P<slug>[:a-zA-Z\-\.\d]+)/$', 'corpus', name='sven_api_corpus'),
  url(r'^.*$', 'not_found', name='sven_api_not_found'),
)

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'sven.views.home', name='home'),
    url(r'^api/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^glue/', include(glue.urls)),
)
