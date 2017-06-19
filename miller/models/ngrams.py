#!/usr/bin/env python
# -*- coding: utf-8 -*-
import string, re
from django.db import models
from django.utils.text import slugify

from miller.models import Document
from django.contrib.postgres.indexes import GinIndex
#PUNCTUATION = re.compile(r'[.;]' % re.escape(string.punctuation))

class Ngrams(models.Model):
  """
  Follow https://www.postgresql.org/docs/9.6/static/pgtrgm.html F.31.5
  """
  slug       = models.CharField(max_length=50, unique=True) # used when creating ngrams instances; the same letters as segment, lowecased.
  segment    = models.CharField(max_length=50) # rough version of segment, without punctuations. See https://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
  frequency  = models.IntegerField(default=1)

  documents  = models.ManyToManyField(Document, blank=True) # where this chunk is present

  class Meta:
    verbose_name_plural = 'a lot of ngrams'
    indexes = [ GinIndex(['segment'])]

  def __unicode__(self):
    return self.segment

  @staticmethod
  def tokenize(text):
    return re.split(r'[\s\-,;\.\?\!\|]+', text) #.translate(dict.fromkeys(map(ord, string.punctuation))))

  @staticmethod
  def find_ngrams(words, n=2):
    return zip(*[words[i:] for i in range(n)])

  @staticmethod
  def slugify(ngrams, max_length=50):
    """
    slugify and cluster ngrams, ready to be stored
    """
    return filter(None, map(lambda x:slugify(x if isinstance(x, basestring) else u' '.join(x))[:max_length], ngrams))