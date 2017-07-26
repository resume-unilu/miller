from __future__ import absolute_import

import logging

from celery import group
from .celery import app

from miller.models import Story, Document

logger = logging.getLogger('miller.celery')

@app.task
def story_update_search_vectors(pk):
  logger.debug('story {pk:%s} update TSV ...' % pk)
  # get list of urls to scrape. Then stuff then change the status
  try:
    story = Story.objects.get(pk=pk)
  except Story.DoesNotExist:
    return None

  story.update_search_vector()
  logger.debug('story {pk:%s, slug:%s} update TSV done.'% (story.pk, story.slug))


@app.task
def document_update_search_vectors(pk):
  logger.debug('document {pk:%s} update TSV ...' % pk)
  # get list of urls to scrape. Then stuff then change the status
  try:
    doc = Document.objects.get(pk=pk)
  except Document.DoesNotExist:
    return None

  doc.update_search_vector()
  logger.debug('doc {pk:%s, slug:%s} update TSV done.'% (doc.pk, doc.slug))