"""sven URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin

import sven.views

urlpatterns = [
  # Examples:
  url(r'^$', sven.views.home, name='sven_home'),
  url(r'^login/$', sven.views.login_view, name='sven_login'),
  url(r'^logout/$', sven.views.logout_view, name='sven_logout'),
  url(r'^admin/', admin.site.urls),
  url(r'^api/', include('sven.api.urls')),
]


if settings.DEBUG:
  from django.conf.urls.static import static
  urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
#   urlpatterns += patterns('django.views.static',
#     (r'media/(?P<path>.*)', 'serve', {'document_root': settings.MEDIA_ROOT}),
#   )