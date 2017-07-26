#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs, logging

from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from miller.models import Story

logger = logging.getLogger('miller.commands')

class Mention(models.Model):
  from_story = models.ForeignKey(Story, related_name='from_mentions', on_delete=models.CASCADE)
  to_story   = models.ForeignKey(Story, related_name='to_mentions', on_delete=models.CASCADE)
  date_created  = models.DateField(auto_now=True)

  class Meta:
    ordering = ["-date_created"]
    verbose_name_plural = "mentions"

  def __unicode__(self):
    return '%s(%s) -> %s(%s)' % (self.from_story.slug, self.from_story.pk, self.to_story.slug, self.to_story.pk)


@receiver(post_save, sender=Mention)
def clear_cache_on_save(sender, instance, created, **kwargs):
  from_story_ckey = instance.from_story.get_cache_key()
  cache.delete(from_story_ckey)
  to_story_ckey = instance.to_story.get_cache_key()
  cache.delete(to_story_ckey)
  logger.debug('mention@post_save {from_story__pk:%s, to_story__pk:%s} story cache cleaned.' % (instance.from_story.pk, instance.to_story.pk))
  
  