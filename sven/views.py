#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext



def home(request):
  d = _shared_context(request)
  return render_to_response("sven/index.html", RequestContext(request, d) )



def _shared_context(request):
  '''
  Return an happy shared contex for your view
  '''
  d = {}
  return d
