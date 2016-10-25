#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Tasks on models
import logging, json

from miller.models import Document

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger('miller.commands')


class Command(BaseCommand):
  help = 'Initialize the JSON field metadata for Story instances'
  

  

  available_tasks = (
    'snapshots', # handle pdf snapshot
    'cleanbin'
  )


  def add_arguments(self, parser):
    parser.add_argument('taskname')


  def handle(self, *args, **options):
    if options['taskname'] in self.available_tasks:
      getattr(self, options['taskname'])(**options)

    logger.debug('command finished.')
    
  def snapshots(self, **options):
    logger.debug('task: snapshots!')

    docs = Document.objects.all()

    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for doc in docs.iterator():
      logger.debug('task: snapshots for {document:%s}' % doc.id)
      try:
        doc.fill_from_url()
        doc.create_snapshot()
        doc.save()
      except Exception as e:
        logger.exception(e)

  #cleaning story.DELETED older than 2 months
  def cleanbin(self, **options):
    logger.debug('task: cleanbin')
      
