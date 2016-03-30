#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs

from django.core.validators import RegexValidator
from django.db import models

from miller import helpers


class Tag(models.Model):
  # categories
  KEYWORD = 'keyword' # i.e, no special category at all
  EVENT   = 'event' # items tagged as events are "news"

  CATEGORY_CHOICES = (
    (KEYWORD, 'keyword'),
    (EVENT, 'event'),
  )

  name       = models.CharField(max_length=32) # e.g. 'Mr. E. Smith'
  slug       = models.SlugField(max_length=32, unique=True) # e.g. 'mr-e-smith'
  category   = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default=KEYWORD) # e.g. 'actor' or 'institution'

  def __unicode__(self):
    return '%s (%s)' % (self.name, self.category)

