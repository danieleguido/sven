from django.contrib import admin
from sven.models import Corpus, Document, Job, Segment, Document_Segment



class DocumentAdmin(admin.ModelAdmin):
  search_fields = ['title', 'slug']
  exclude = ['slug', 'mimetype']



class CorpusAdmin(admin.ModelAdmin):
  search_fields = ['name']


class JobAdmin(admin.ModelAdmin):
  search_fields = ['corpus']


class SegmentAdmin(admin.ModelAdmin):
  search_fields = ['lemmata']


admin.site.register(Document, DocumentAdmin)
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Segment, SegmentAdmin)
admin.site.register(Document_Segment)