#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs,json,logging

from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import pre_delete, post_save, m2m_changed, pre_save
from django.dispatch import receiver

from miller import helpers

logger = logging.getLogger('miller.commands')



class Page(models.Model):
  """
  Model to fill static page from within the admin instead of using the client (a more robust approach)
  """
  name       = models.CharField(max_length=100) # e.g. 'Mr. E. Smith'
  slug       = models.SlugField(max_length=100, unique=True) # e.g. 'mr-e-smith'
  contents   = models.TextField(verbose_name=u'mardown content',default='',blank=True) # It will store markdown contents, everything.
  
  def __unicode__(self):
    return '%s' % (self.name)



@receiver(pre_save, sender=Page)
def complete_instance(sender, instance, **kwargs):
  logger.debug('page {pk:%s} @pre_save' % instance.pk)
  if not instance.slug:
    instance.slug = helpers.get_unique_slug(instance, instance.name, max_length=32)
    logger.debug('page {pk:%s, slug:%s} @pre_save slug generated' % (instance.pk, instance.slug))

