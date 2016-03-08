#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json

#
#  test stopwords and pattern chunking.
#  python manage.py test sven.test.distiller.DistillerTest --testrunner=sven.test.NoDbTestRunner
#
from django.test import SimpleTestCase

from sven.distiller import distill, EN_STOPWORDS


class DistillerTest(SimpleTestCase):
  def test_distill(self):
    content = u'''
      2.4.  Tunisia’s Jasmine Revolution and the End of the Ancien Régime.

      Millions of Tunisians are casting to directly elect their president for the first time since the revolution four years ago that swept away longtime leader Zine El Abidine Ben Ali.
    '''
    results = distill(content=content, language="en", stopwords=EN_STOPWORDS, query='NP')
    self.assertEqual(len(results), 10)
    # results = [(u'the Ancien R\xe9gime', u'ancien r\xe9gime', 0.3333333333333333, 0.4150374992788437), (u'the End', u'end', 0.3333333333333333, 0.4150374992788437), (u'2.4.\xa0 Tunisia \u2019 s Jasmine Revolution', u'jasmine revolution tunisia', 0.3333333333333333, 0.4150374992788437)]
    #
    #print results