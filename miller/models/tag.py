#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs,json

from django.conf import settings
from django.core.validators import RegexValidator
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models.functions import Cast
from django.utils.text import slugify
from miller import helpers



class Tag(models.Model):
  # categories
  KEYWORD = 'keyword' # i.e, no special category at all
  BLOG   = 'blog' # items tagged as events are "news"
  HIGHLIGHTS   = 'highlights'
  WRITING      = 'writing'
  COLLECTION   = 'collection'
  PUBLISHING   = 'publishing' # things related to publishing activity, I.E issue number that can be filtered by

  CATEGORY_CHOICES = (
    (KEYWORD, 'keyword'),
    (BLOG, 'blog'),
    (HIGHLIGHTS, 'highlights'),
    (WRITING, 'writing'),
    (COLLECTION, 'collection'),
    (PUBLISHING, 'publishing')
  ) + settings.MILLER_TAG_CATEGORY_CHOICES

  HIDDEN  = 'hidden'
  PUBLIC  = 'public' # everyone can access that.

  STATUS_CHOICES = (
    (HIDDEN, 'keep this hidden'),
    (PUBLIC, 'published tag'),
  )

  name       = models.CharField(max_length=100) # e.g. 'Mr. E. Smith'
  slug       = models.SlugField(max_length=100, unique=True, blank=True) # e.g. 'mr-e-smith'
  category   = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default=KEYWORD) # e.g. 'actor' or 'institution'
  status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PUBLIC)

  data       = JSONField(default=dict)

  # search     = models.TextField(null=True, blank=True)# SearchVectorField(null=True, blank=True) # index search
  
  class Meta:
    unique_together = ('name', 'category')

  def __unicode__(self):
    return '%s (%s)' % (self.name, self.category)


  @staticmethod
  def get_search_Q(query):
    """
    Return search queryset for this model. Generate Q fields for each language This follows: https://stackoverflow.com/questions/852414/how-to-dynamically-compose-an-or-query-filter-in-django
    """
    queries = [models.Q(**{'data__name__%s__icontains' % lang[2]: query}) for lang in settings.LANGUAGES] + [
      models.Q(slug__icontains=query),
      models.Q(name__icontains=query)
    ]
    q = queries.pop()
    for item in queries:
      q |= item
    return q


  def save(self, *args, **kwargs):
    if not self.slug:
      self.slug = helpers.get_unique_slug(self, self.name, 100)

    # for a in settings.LANGUAGES:
    #   config_language = a[3]
    # self.search = SearchVector('name', weight='A', config='simple')

    super(Tag, self).save(*args, **kwargs)
