#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json

#
#  test stopwords and pattern chunking.
#  python manage.py test sven.test.distiller.DistillerTest --testrunner=sven.test.NoDbTestRunner
#
from django.test import TestCase

from sven.distiller import distill, EN_STOPWORDS


class DistillerTest(TestCase):
  def test_distill(self):
    content = u'''
      2.4.  Tunisia’s Jasmine Revolution and the End of the Ancien Régime.
    '''

    #   Millions of Tunisians are casting to directly elect their president for the first time since the revolution four years ago that swept away longtime leader Zine El Abidine Ben Ali.



    #   Sunday's election will be a closely fought contest among stalwarts of the deposed regime, members of the once-outlawed parties, as well as a new breed of politicians that has emerged since the 2011 revolution. Early voter turnout after the opening of the polling stations at 8am local time (07:00 GMT) was low, especially among the youth. Al Jazeera visited a polling centre at 18 Rue de L'Inde in Lafayette district in downtown Tunis, where the voting process was progressing smoothly. "As you can see it is a very smooth and calm operation. So far things have been going very well," Noureddine Jouini, the electoral officer in charge of the polling station, told Al Jazeera. "Last time in the legislative elections there were a couple of people who couldn't find their names on the lists even though they had registered. This time the lists have been updated and we have not received any complaints regarding that issue. The youth voter turnout is very low like in the legislative," Jouini said. Mohamed Khlil, 78, a retired state official, was among the first to vote in the early hours.



    #   "I came to vote because it's my country's fate that we are deciding. I am very happy to be able to vote and make my voice heard," Khlil told Al Jazeera after casting his vote in the same polling station. Youth absence



    #   The voters themselves noticed the absence of young people from polling booths.
    # ''' 

    results = distill(content=content, language="en", stopwords=EN_STOPWORDS, query='NP')
    print results