from django.conf.urls import patterns, include, url

from django.contrib import admin

import glue.urls

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'sven.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^glue/', include(glue.urls)),
)
