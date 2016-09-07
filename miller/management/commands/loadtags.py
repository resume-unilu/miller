#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, json, unicodecsv, io

from miller.models import Tag

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

logger = logging.getLogger('miller.commands')


class Command(BaseCommand):
  help = 'Load a csv file of tags according to Tag model. Csv rows MUST have "slug" and "name" fields'

  def add_arguments(self, parser):
    pass

  def handle(self, *args, **options):
    with open('/Users/danieleguido/tools/resume/AEL.tsv') as file:
      r = unicodecsv.DictReader(file, delimiter='\t')
      with transaction.atomic():  
        for row in r:
          tag, created = Tag.objects.get_or_create(category=Tag.KEYWORD, name=row['name'],slug=row['slug']);
          print created, tag

    logger.debug('command finished.')
      
