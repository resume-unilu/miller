#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from codemirror import CodeMirrorTextarea

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from miller.models import Profile, Story, Tag, Document, Caption


class WritingTagsListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('type of writing')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'type-of-writing'

    def lookups(self, request, model_admin):
        
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return Tag.objects.filter(category=Tag.WRITING).values_list('slug', 'name')
        

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() is None:
          return queryset
        return queryset.filter(tags__category=Tag.WRITING, tags__slug=self.value())

# Define an inline admin descriptor for Profile model
# which acts a bit like a singleton
class ProfileInline(admin.StackedInline):
  model = Profile
  can_delete = False
  verbose_name_plural = 'profiles'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
  inlines = (ProfileInline, )


class DocumentAdminForm(forms.ModelForm):
  def __init__(self, *args, **kwargs):
    codemirror_widget = CodeMirrorTextarea(mode="python", theme="default", config={ 
      'fixedGutter': True, 
      'lineNumbers':True, 
      'lineWrapping': True
    })
    super(DocumentAdminForm, self).__init__(*args, **kwargs)
    self.fields['contents'].widget = codemirror_widget

  def clean_contents(self):
    try:
      contents = json.loads(self.cleaned_data['contents'])
    except ValueError as e:
      raise forms.ValidationError(u'%s'%e)
      # Expecting property name enclosed in double quotes: line 14 column 5 (char 1275)
    
    return self.cleaned_data['contents']

class DocumentAdmin(admin.ModelAdmin):
  search_fields = ['title', 'contents']
  exclude=['snapshot', 'copyright']
  list_filter = ('type',)
  form = DocumentAdminForm

class CaptionAdmin(admin.ModelAdmin):
  search_fields = ['contents']


class CaptionInline(admin.TabularInline):
  model = Caption
  extra = 2 # how many rows to show

class StoryAdmin(admin.ModelAdmin):
  # inlines = (CaptionInline,)
  exclude=['cover', 'cover_copyright', 'watchers']
  search_fields = ['title']
  list_filter = (WritingTagsListFilter,)


class TagAdmin(admin.ModelAdmin):
  search_fields = ['name', 'slug', 'category']
  list_filter = ('category',)





# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Story, StoryAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Caption, CaptionAdmin)