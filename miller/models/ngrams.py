#!/usr/bin/env python
# -*- coding: utf-8 -*-
import string, re
from django.db import models
from django.utils.text import slugify

from miller.models import Document
from django.contrib.postgres.indexes import GinIndex
#PUNCTUATION = re.compile(r'[.;]' % re.escape(string.punctuation))

# slug common stopword list for single grams, l > 2.



class Ngrams(models.Model):
  COMMON_STOPWORDS = [
    'the',
    'each',
    'and',
    'for',
    'sur',
    'pour',
    'dans',
    'with',
    'from',
    'other',
    'une',
    'les',
    'are',
    'has',
    'may',
    'its',
    'est',
    'after',
    'aux'
  ]

  MIN_SLUG_LENGTH = 3
  MAX_SLUG_LENGTH = 32

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
  def punktSentenceTokenize(text):
    """
    very basic tokenizer. @todo: It may use nltk if nltk is available.
    """
    import imp
    try:
      imp.find_module('nltk')
      import nltk
      sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
      return sent_detector.tokenize(text.strip())
    except ImportError:
      return re.split(r'[;?\!\|\.]+', text)


  @staticmethod
  def find_ngrams(words, n=2):
    return zip(*[words[i:] for i in range(n)])


  @staticmethod
  def filter_prepared_ngrams(ngram):
    l = len(ngram['slug'])
    if ngram['slug'] is None or ngram['slug'].isdigit():
      return False
    return l >= Ngrams.MIN_SLUG_LENGTH and l <= Ngrams.MAX_SLUG_LENGTH


  @staticmethod
  def prepare(ngrams):
    """
    slugify and cluster ngrams, ready to be stored
    """
    return filter(Ngrams.filter_prepared_ngrams, map(lambda x:{'slug':slugify(x if isinstance(x, basestring) else u' '.join(x)), 'segment': u' '.join(x)}, ngrams))



