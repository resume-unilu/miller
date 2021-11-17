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
        print "Get the tag Revue de l'Euro"
        try:
            rde = Tag.objects.filter(category='writing', slug='revue-ecu-euro').get()
        except Tag.objects.DoesNotExist:
            print "Tag Revue de l'Euro not found... Only global statistics will be generated"
            rde = None

        print 'Analyze stories...'
        tags_usages = defaultdict(int)
        euro_tags_usages = defaultdict(int)
        for story in Story.objects.all():
            euro_article = False if rde is None else rde in story.tags.all()
            pool = euro_tags_usages if euro_article else tags_usages
            for keyword in story.tags.filter(category='keyword'):
                pool[keyword.id] += 1
        print 'Statistics for {} tags gathered'.format(len(tags_usages) + len(euro_tags_usages))

        with transaction.atomic():
            for keyword in Tag.objects.filter(category='keyword'):
                keyword.usage_statistics = tags_usages[keyword.id]
                keyword.euro_usage_statistics = euro_tags_usages[keyword.id]
                keyword.save()
        print 'Tags usage saved in database'

