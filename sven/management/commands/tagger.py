#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Temporary
#
from django.core.management.base import BaseCommand
from sven.models import Document, Tag, Corpus
from django.db import transaction

class Command(BaseCommand):


  def handle(self, *args, **options):
    corpora = Corpus.objects.all()

    # get corpus tag
    # get or create corresponding tags for the given corpus
    for cor in corpora:
      # get the corpus documents
      documents = Document.objects.get(corpus=cor)

      for doc in documents:
        # get the document tags
        tags = doc.tags.all()

        # get or create specific tag for the corpus
        

        # clone and attache the cloned version

