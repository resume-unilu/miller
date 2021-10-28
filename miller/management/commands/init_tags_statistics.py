#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict
import logging, json, unicodecsv, io

from miller.models import Tag, Story

from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger('miller.commands')


class Command(BaseCommand):
    help = 'Init tags (only keywords for now) usage counts. Command can be used at anytime to reset the Tag.usage_statistics value'

    def handle(self, *args, **options):
        print 'Analyze stories...'
        tags_usages = defaultdict(int)
        for story in Story.objects.all():
            for keyword in story.tags.filter(category='keyword'):
                tags_usages[keyword.id] += 1

        print 'Statistics for {} tags gathered'.format(len(tags_usages))

        with transaction.atomic():
            for keyword in Tag.objects.filter(category='keyword'):
                keyword.usage_statistics = tags_usages[keyword.id]
                keyword.save()
        print 'Tags usage saved in database'

