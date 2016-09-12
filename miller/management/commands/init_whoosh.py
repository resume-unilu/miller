#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from miller.helpers import get_whoosh_index, search_whoosh_index
from miller.models import Story, Document
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger('miller.commands')


class Command(BaseCommand):
  help = 'Initialize and updatet the whoosh index'

  def add_arguments(self, parser):
    pass

  def handle(self, *args, **options):
    logger.debug('looking for a whoosh index')
    ix = get_whoosh_index()
    logger.debug('whoosh index available! Updating ...')
    
    stories = Story.objects.all()

    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for story in stories.iterator():
      logger.debug('storing story id: %s' % story.id)
      try:
        story.store(ix=ix)
      except Exception as e:
        logger.exception(e)
        break
      else:
        logger.debug('storing story id: %s success' % story.id)
      

    docs = Document.objects.all()

    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for story in docs.iterator():
      logger.debug('storing story id: %s' % story.id)
      try:
        story.store(ix=ix)
      except Exception as e:
        logger.exception(e)
        break
      else:
        logger.debug('storing story id: %s success' % story.id)
      
