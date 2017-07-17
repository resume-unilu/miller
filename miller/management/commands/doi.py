#!/usr/bin/env python
# -*- coding: utf-8 -*-
# special tasks for DOI
import logging
import pydash as pyd

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.db import transaction

from miller.doi import DataciteDOI, DataciteDOIMetadata
from miller.management.commands.task import Command as TaskCommand
#from miller.management.commands import utils
from miller.models import Story


logger = logging.getLogger('console')


class Command(TaskCommand):
  """
  Usage sample: 
  python manage.py doi retrieve_doi --pk=991
  """
  help = 'A lot of tasks dealing with biographical data'
  

  available_tasks = (
    'create_doi',
    'retrieve_doi',

    'create_metadata',
    'retrieve_metadata'
  )


  def create_doi(self, pk, **options):
    qpk = {'pk': pk} if pk.isdigit() else {'slug': pk}
    story = Story.objects.get(**qpk)

    d = DataciteDOI(story=story)
    logger.debug(d.config())
    logger.debug('creating: %s' %d._log_prefix())
    res = d.create()
    
    story.data['doi'] = d.format()
    story.save()
    
    logger.debug(res)


  def retrieve_doi(self, pk, **options):
    """
    return DOI url
    """
    qpk = {'pk': pk} if pk.isdigit() else {'slug': pk}
    story = Story.objects.get(**qpk)

    d = DataciteDOI(story=story)
    logger.debug(d.retrieve())


  def create_metadata(self, pk, **options):
    qpk = {'pk': pk} if pk.isdigit() else {'slug': pk}
    story = Story.objects.get(**qpk)

    d = DataciteDOIMetadata(story=story)
    logger.debug(d.config())
    res = d.create()
    logger.debug(res)


  def retrieve_metadata(self, pk, **options):
    qpk = {'pk': pk} if pk.isdigit() else {'slug': pk}
    story = Story.objects.get(**qpk)

    d = DataciteDOIMetadata(story=story)
    logger.debug(d.retrieve())



