#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from miller.models import Profile, Story, Tag, Document, Caption

# Define an inline admin descriptor for Profile model
# which acts a bit like a singleton
class ProfileInline(admin.StackedInline):
  model = Profile
  can_delete = False
  verbose_name_plural = 'profiles'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
  inlines = (ProfileInline, )

class DocumentAdmin(admin.ModelAdmin):
  search_fields = ['title', 'contents']
  exclude=['snapshot']
  list_filter = ('type',)

class CaptionAdmin(admin.ModelAdmin):
  search_fields = ['contents']


class CaptionInline(admin.TabularInline):
  model = Caption
  extra = 2 # how many rows to show

class StoryAdmin(admin.ModelAdmin):
  inlines = (CaptionInline,)
  search_fields = ['title']
  list_filter = ('tags',)


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