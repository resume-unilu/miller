#!/usr/bin/env python
# -*- coding: utf-8 -*-
# special tasks for biographical data
import logging
import pydash as pyd

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count

from miller.management.commands.task import Command as TaskCommand
from miller.management.commands import utils
from miller.models import Document, Story, Ngrams

logger = logging.getLogger('console')


class Command(TaskCommand):
  """
  Usage sample: 
  python manage.py task snapshot --pk=991
  """
  help = 'A lot of tasks dealing with ngrams and Postgres vectors'
  

  available_tasks = (
    'search_ngrams_table',
    'update_search_vectors',
    'update_ngrams_table',
    'clean_ngrams_table'
  )

  def add_arguments(self, parser):
    super(Command, self).add_arguments(parser)
    parser.add_argument(
        '--query',
        dest='query',
        default=None,
        help='query for search vectors',
    )


  def clean_ngrams_table(self, **options):
    """
    Remove unused ngrams from ngrams table.
    Usage: 
    python manage.py task clean_ngrams_table
    """
    logger.debug('task: clean_ngrams_table')
    logger.debug('... total: %s ngrams' % Ngrams.objects.count())
    
    ngr = Ngrams.objects.annotate(num_documents=Count('documents'))

    print ngr.filter(num_documents=0).delete()
    # logger.debug('... deleting ngrams, %s' % 
    logger.debug('... now %s ngrams in table after deleting leaves.' % Ngrams.objects.count())

    for ngr in ngr.order_by('-num_documents')[:100]:
      print ngr.segment, ngr.slug, ngr.num_documents



  def search_ngrams_table(self, query=None, model=False, **options):
    """
    Test ngrams table contents.
    Usage: 
    python manage.py task search_ngrams_table --query=alaska
    """
    logger.debug('task: search_ngrams_table')
    if not query:
      raise Exception('please specify a valid search query using the --query parameter')

    if model == 'document':
      from django.contrib.postgres.search import SearchVector
      from django.contrib.postgres.search import TrigramSimilarity
      # provided a q 
      logger.debug(u'using "%s"' % query)
    
      ngrams = Document.objects.annotate(
        similarity=TrigramSimilarity('ngrams__segment', query),
      ).filter(similarity__gt=0.35).order_by('-similarity').values('ngrams__segment', 'ngrams__slug').distinct()[:10]

      for n in ngrams:
        logger.debug(u'- %s (%s)' % (n.get('ngrams__segment'), n.get('ngrams__slug')))
      



  def update_search_vectors(self, pk=None, model=False, **options):
    logger.debug('task: update_search_vectors')

    if model == 'document':
      docs = Document.objects.all()
      if pk:
        docs = docs.filter(pk=pk)
      for doc in docs.iterator():
        doc.update_search_vector()
        logger.debug('task: update_search_vectors for document {pk:%s, slug:%s}' % (doc.pk, doc.slug))
    elif model == 'story':
      stories = Story.objects.exclude(status=Story.DELETED)
      if pk:
        stories = stories.filter(pk=pk)
      for story in stories.iterator():
        story.update_search_vector()
        logger.debug('task: update_search_vectors for story {pk:%s, slug:%s}' % (story.pk, story.slug))
    else:
      logger.error('task: please provide a valid model to update_whoosh: "document" or "story"...')
  

  def update_ngrams_table(self, pk=None, model=False, **options):
    """
    Example usage:
    python manage.py task update_ngrams_table --model=document --pk=984
    """
    logger.debug('task: update_ngrams_table')
    if model == 'document':
      docs = Document.objects.all()

      if pk:
        god = {'pk':pk} if pk.isdigit() else {'slug':pk}
        docs = docs.filter(**god)
      for doc in docs.iterator():
        logger.debug('task: update_search_vectors for document {pk:%s, slug:%s}' % (doc.pk, doc.slug))
        doc.ngrams_set.clear()
        indexed_contents = doc.update_search_vector()

        sentences = Ngrams.punktSentenceTokenize(u'.\n'.join([idx[0] for idx in indexed_contents]))
        
        logger.debug('  - sentences: %s' % len(sentences))
        if pk:
          print sentences

        for ids, s in enumerate(sentences):
          words = Ngrams.tokenize(s)


          ngs   = Ngrams.find_ngrams(words=words, n=1) + Ngrams.find_ngrams(words=words, n=2)# + Ngrams.find_ngrams(words=words, n=3)
          ngs   = Ngrams.prepare(ngs)

          logger.debug('  ... %s/%s, found %s ngrams' % (ids+1, len(sentences), len(ngs)))
          # pseudo bulk_create
          for idx, ngram in enumerate(ngs):
            # stopwords? or directly in grams slugify function
            if ngram['slug'] in Ngrams.COMMON_STOPWORDS:
              print ' skipping, is a stopword', ngram['segment'], ngram['slug']
              continue

            if pk:
              logger.debug('    %s %s (%s)' % (idx, ngram['segment'], ngram['slug']))
            
            try:
              ng, created = Ngrams.objects.get_or_create(slug=ngram['slug'], defaults={
                'segment': ngram['segment']
              })
              doc.ngrams_set.add(ng)
            except Exception as e:
              raise e
              #else:
              #  logger.debug('  ... idx: %s, slug:%s, created:%s' % (idx, slug, created))
        if sentences:
          doc.save()

      # clear all ngrams that do not belong to any documents
      



