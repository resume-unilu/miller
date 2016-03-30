#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from miller.models import Profile, Story, Tag

# Define an inline admin descriptor for Profile model
# which acts a bit like a singleton
class ProfileInline(admin.StackedInline):
  model = Profile
  can_delete = False
  verbose_name_plural = 'profiles'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
  inlines = (ProfileInline, )

class StoryAdmin(admin.ModelAdmin):
  search_field = ['title']

class TagAdmin(admin.ModelAdmin):
  search_field = ['name', 'slug', 'category']

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Story, StoryAdmin)