#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, json

from miller.models import Story, Tag

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger('miller.commands')


class Command(BaseCommand):
  help = 'Initialize the JSON field metadata for Story instances'

  def add_arguments(self, parser):
    pass

  def handle(self, *args, **options):
    
    stories = Story.objects.filter(metadata=u'{}')

    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for story in stories.iterator():
      logger.debug('reconcile metadata of story id: %s' % story.id)
      story.save()
    
    logger.debug('story finished.')
      
    tags = Tag.objects.all()

    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for tag in tags.iterator():
      logger.debug('reconcile metadata of tag id: %s' % tag.id)
      tag.save()
    
    logger.debug('command finished.')
      
