from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from sven.models import Corpus, Document, Tag, Job, Segment, Document_Segment, Profile



class DocumentAdmin(admin.ModelAdmin):
  search_fields = ['title', 'slug']
  exclude = ['slug', 'mimetype']



class CorpusAdmin(admin.ModelAdmin):
  search_fields = ['name']
  exclude = ['slug']

 



class JobAdmin(admin.ModelAdmin):
  search_fields = ['corpus']



class TagAdmin(admin.ModelAdmin):
  search_fields = ['name']
  list_filter = ('type',)


class SegmentAdmin(admin.ModelAdmin):
  search_fields = ['lemmata']



class ProfileInline(admin.StackedInline):
  model = Profile
  can_delete = False
  verbose_name_plural = 'profiles'



class UserAdmin(UserAdmin):
  pass
  #inlines = (ProfileInline, )



admin.site.register(Document, DocumentAdmin)
admin.site.register(Corpus, CorpusAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Segment, SegmentAdmin)
admin.site.register(Document_Segment)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)