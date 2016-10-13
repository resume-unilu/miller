#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs

from django.db import models
from miller.models import Story

class Mention(models.Model):
  from_story = models.ForeignKey(Story, related_name='from_mentions', on_delete=models.CASCADE)
  to_story   = models.ForeignKey(Story, related_name='to_mentions', on_delete=models.CASCADE)
  date_created  = models.DateField(auto_now=True)

  class Meta:
    ordering = ["-date_created"]
    verbose_name_plural = "mentions"

  def __unicode__(self):
    return '%s(%s) -> %s(%s)' % (self.from_story.slug, self.from_story.pk, self.to_story.slug, self.to_story.pk)