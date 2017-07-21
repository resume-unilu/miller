#!/usr/bin/env python
# -*- coding: utf-8 -*-
import string, re

from collections import deque

from django.db import models
from django.utils.text import slugify

from miller.models import Document
from django.contrib.postgres.indexes import GinIndex
#PUNCTUATION = re.compile(r'[.;]' % re.escape(string.punctuation))

# slug common stopword list for single grams, l > 2.

APOSTROPHE    = re.compile(ur'[’\'"]+', re.UNICODE)


WORD_TOKENIZE = re.compile(ur'[\s\-,;:\.\?\!\|\{\(\)\}\[\]]+', re.UNICODE)
SLUG_STRIP    = re.compile(r'^\s?[_\-]+\s?|\s?[_\-]+\s?$')

MIN_SLUG_LENGTH = 3
MAX_SLUG_LENGTH = 32

ENGLISH_STOPWORDS = [u'a',u'about',u'above',u'after',u'again',u'against',u'all',u'am',u'an',u'and',u'any',u'are',u'aren\'t',u'as',u'at',u'be',u'because',u'been',u'before',u'being',u'below',u'between',u'both',u'but',u'by',u'can\'t',u'cannot',u'could',u'couldn\'t',u'did',u'didn\'t',u'do',u'does',u'doesn\'t',u'doing',u'don\'t',u'down',u'during',u'each',u'few',u'for',u'from',u'further',u'had',u'hadn\'t',u'has',u'hasn\'t',u'have',u'haven\'t',u'having',u'he',u'he\'d',u'he\'ll',u'he\'s',u'her',u'here',u'here\'s',u'hers',u'herself',u'him',u'himself',u'his',u'how',u'how\'s',u'i',u'i\'d',u'i\'ll',u'i\'m',u'i\'ve',u'if',u'in',u'into',u'is',u'isn\'t',u'it',u'it\'s',u'its',u'itself',u'let\'s',u'me',u'more',u'most',u'mustn\'t',u'my',u'myself',u'no',u'nor',u'not',u'of',u'off',u'on',u'once',u'only',u'or',u'other',u'ought',u'our',u'ours',u'ourselves',u'out',u'over',u'own',u'same',u'shan\'t',u'she',u'she\'d',u'she\'ll',u'she\'s',u'should',u'shouldn\'t',u'so',u'some',u'such',u'than',u'that',u'that\'s',u'the',u'their',u'theirs',u'them',u'themselves',u'then',u'there',u'there\'s',u'these',u'they',u'they\'d',u'they\'ll',u'they\'re',u'they\'ve',u'this',u'those',u'through',u'to',u'too',u'under',u'until',u'up',u'very',u'was',u'wasn\'t',u'we',u'we\'d',u'we\'ll',u'we\'re',u'we\'ve',u'were',u'weren\'t',u'what',u'what\'s',u'when',u'when\'s',u'where',u'where\'s',u'which',u'while',u'who',u'who\'s',u'whom',u'why',u'why\'s',u'with',u'won\'t',u'would',u'wouldn\'t',u'you',u'you\'d',u'you\'ll',u'you\'re',u'you\'ve',u'your',u'yours',u'yourself',u'yourselves'
]

FRENCH_STOPWORDS = [u'alors',u'au',u'aucuns',u'aussi',u'autre',u'avant',u'avec',u'avoir',u'bon',u'car',u'ce',u'cela',u'ces',u'c\'est',u'ceux',u'chaque',u'ci',u'comme',u'comment',u'dans',u'des',u'du',u'dedans',u'dehors',u'depuis',u'devrait',u'doit',u'donc',u'dos',u'début',u'elle',u'elles',u'en',u'encore',u'essai',u'est',u'et',u'eu',u'fait',u'faites',u'fois',u'font',u'hors',u'ici',u'il',u'ils',u'je',u'juste',u'la',u'le',u'les',u'leur',u'là',u'ma',u'maintenant',u'mais',u'mes',u'mine',u'moins',u'mon',u'mot',u'même',u'ni',u'nommés',u'notre',u'nous',u'ou',u'où',u'par',u'parce',u'pas',u'peut',u'peu',u'plupart',u'pour',u'pourquoi',u'quand',u'que',u'quel',u'quelle',u'quelles',u'quels',u'qui',u'sa',u'sans',u'ses',u'seulement',u'si',u'sien',u'son',u'sont',u'sous',u'soyez',u'sur',u'ta',u'tandis',u'tellement',u'tels',u'tes',u'ton',u'tous',u'tout',u'trop',u'très',u'tu',u'voient',u'vont',u'votre',u'vous',u'vu',u'ça',u'étaient',u'état',u'étions',u'été',u'être'
]

GERMAN_STOPWORDS = [u'aber',u'als',u'am',u'an',u'auch',u'auf',u'aus',u'bei',u'bin',u'bis',u'bist',u'da',u'dadurch',u'daher',u'darum',u'das',u'daß',u'dass',u'dein',u'deine',u'dem',u'den',u'der',u'des',u'dessen',u'deshalb',u'die',u'dies',u'dieser',u'dieses',u'doch',u'dort',u'du',u'durch',u'ein',u'eine',u'einem',u'einen',u'einer',u'eines',u'er',u'es',u'euer',u'eure',u'für',u'hatte',u'hatten',u'hattest',u'hattet',u'hier',u'hinter',u'ich',u'ihr',u'ihre',u'im',u'in',u'ist',u'ja',u'jede',u'jedem',u'jeden',u'jeder',u'jedes',u'jener',u'jenes',u'jetzt',u'kann',u'kannst',u'können',u'könnt',u'machen',u'mein',u'meine',u'mit',u'muß',u'mußt',u'musst',u'müssen',u'müßt',u'nach',u'nachdem',u'nein',u'nicht',u'nun',u'oder',u'seid',u'sein',u'seine',u'sich',u'sie',u'sind',u'soll',u'sollen',u'sollst',u'sollt',u'sonst',u'soweit',u'sowie',u'und',u'unser',u'unsere',u'unter',u'vom',u'von',u'vor',u'wann',u'warum',u'was',u'weiter',u'weitere',u'wenn',u'wer',u'werde',u'werden',u'werdet',u'weshalb',u'wie',u'wieder',u'wieso',u'wir',u'wird',u'wirst',u'wo',u'woher',u'wohin',u'zu',u'zum',u'zur',u'über'
]

WEB_STOPWORDS = [
  'https', 'ftp'
]
COMMON_STOPWORDS = ENGLISH_STOPWORDS + FRENCH_STOPWORDS + GERMAN_STOPWORDS + WEB_STOPWORDS

def filter_prepared_ngrams(ngram):
  return bool(ngram['slug'])


def map_simplify_ngrams(ngrams):
  """
  if negrams is iterable, eliminate edges if they match a word on the top list (or if they're empty)
  """
  _ngrams = deque(ngrams)

  while _ngrams and (_ngrams[0].lower() in COMMON_STOPWORDS or len(_ngrams[0]) < MIN_SLUG_LENGTH or len(_ngrams[0]) > MAX_SLUG_LENGTH ):
    _ngrams.popleft()

  while _ngrams and (_ngrams[-1].lower() in COMMON_STOPWORDS or len(_ngrams[-1]) < MIN_SLUG_LENGTH or len(_ngrams[-1]) > MAX_SLUG_LENGTH ):
    _ngrams.pop()

  _ngrams = filter(None,_ngrams)
  #print 'simplified', _ngrams, 'from', ngrams

  return _ngrams

def map_prepared_ngrams(ngram):
  """
  Should be iterable.
  """
  # is iterable
  segment = u' '.join(ngram)
  slug = u'-'.join(filter(None,[slugify(APOSTROPHE.sub('_', n), allow_unicode=True) for n in ngram]))

  return {
    'slug': SLUG_STRIP.sub('', slug),
    'segment': segment.strip()
  }


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
    """
    split words
    """
    return WORD_TOKENIZE.split(text)#APOSTROPHE.sub('_', text))
    #return re.split(, text.prelace('’','')) #.translate(dict.fromkeys(map(ord, string.punctuation))))

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




    #x:{'slug':slugify(APOSTROPHE.sub('_', x) if isinstance(x, basestring) else u' '.join(x)), 'segment': u' '.join(x)}


  @staticmethod
  def prepare(ngrams):
    """
    slugify and cluster ngrams, ready to be stored.
    Works only with tokens
    """
    return filter(filter_prepared_ngrams, map(map_prepared_ngrams, map(map_simplify_ngrams, ngrams)))



