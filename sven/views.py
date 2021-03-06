#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.utils.translation import ugettext as _
from django.template import RequestContext

from sven.forms import LoginForm
from sven.models import Document, Corpus


@login_required
def home(request):
  d = _shared_context(request)

  cor = Corpus.objects.filter(owners=request.user)[0]
  d['corpus'] = cor.pk
  return render_to_response("index.html", RequestContext(request, d))



@staff_member_required
def home_dev(request):
  '''
  this is the current dev angular ome pèage.
  Visible only by admins
  '''
  d = _shared_context(request)
  return render_to_response("index.dev.html", RequestContext(request, d))



def login_view(request):
  if request.user.is_authenticated():
    return home(request)

  form = LoginForm(request.POST)
  next = request.REQUEST.get('next', 'sven_home')

  login_message = {
    'next': next if len( next ) else 'sven_home'
  }

  if request.method != 'POST':
    d = _shared_context(request, tags=[ "login" ], d=login_message)
    return render_to_response('login.html', RequestContext(request, d ))

  if not request.POST.get('remember_me', None):
    request.session.set_expiry(0)

  if form.is_valid():
    user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
    if user is not None:
      if user.is_active:
        login(request, user)
        # @todo: Redirect to next page

        return redirect(login_message['next'])
      else:
        login_message['error'] = _("user has been disabled")
    else:
      login_message['error'] = _("invalid credentials")
      # Return a 'disabled account' error message
  else:
    login_message['error'] = _("invalid credentials")
    login_message['invalid_fields'] = form.errors
  
  d = _shared_context( request, tags=[ "login" ], d=login_message )
  return render_to_response('login.html', RequestContext(request, d ) )



def logout_view( request ):
  logout( request )
  return redirect( 'sven_home' )



def _shared_context(request, tags=[], d={}):
  '''
  Return an happy shared contex for your view
  '''
  d.update({
    'SVEN_NAME': settings.SVEN_NAME,
    'DEBUG': settings.DEBUG,
    'ENABLE_CDN_SERVICES': settings.ENABLE_CDN_SERVICES,
    'LANGUAGE': request.LANGUAGE_CODE,
    'BASE_URL': settings.BASE_URL
  })
  return d
