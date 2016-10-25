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
    'snapshot', # require document pk
    'snapshots', # handle pdf snapshot
    'cleanbin'
  )


  def add_arguments(self, parser):
    parser.add_argument('taskname')
    # Named (optional) arguments
    parser.add_argument(
        '--pk',
        dest='pk',
        default=False,
        help='primary key of the instance',
    )

  def handle(self, *args, **options):
    if options['taskname'] in self.available_tasks:
      getattr(self, options['taskname'])(**options)

    logger.debug('command finished.')
  
  def snapshot(self, **options):
    logger.debug('task: snapshot!')
    if not options['pk']:
      raise Exception('--pk not found')
    
    logger.debug('task: snapshot for {document:%s}' % options['pk'])

    doc = Document.objects.get(pk=options['pk'])
    try:
      doc.fill_from_url()
      doc.create_snapshot()
      doc.save()
    except Exception as e:
      logger.exception(e)

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
      
