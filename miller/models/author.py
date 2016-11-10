#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, json

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from miller import helpers

logger = logging.getLogger('miller')


class Author(models.Model):
  fullname    = models.TextField()
  affiliation = models.TextField(null=True, blank=True) # e.g Government and Politics, University of Luxembpourg
  metadata    = models.TextField(null=True, blank=True, default=json.dumps({
    'firstname': '',
    'lastname': ''
  }, indent=1))
  slug        = models.CharField(max_length=140, unique=True, blank=True)
  user        = models.ForeignKey(User, related_name='authorship', blank=True, null=True, on_delete=models.CASCADE)

  class Meta:
    app_label="miller"

  def save(self, *args, **kwargs):
    if not self.pk and not self.slug:
      self.slug = helpers.get_unique_slug(self, self.fullname)
    super(Author, self).save(*args, **kwargs)

      


@receiver(post_save, sender=User)
def create_author(sender, instance, created, **kwargs):
  logger.debug('(user {pk:%s}) @post_save.' % instance.pk)

  if created or instance.authorship.count() == 0:
    fullname = u'%s %s' % (instance.first_name, instance.last_name) if instance.first_name else instance.username
    aut = Author(user=instance, fullname=fullname, metadata=json.dumps({
      'firstname': instance.first_name,
      'lastname': instance.last_name
    }, indent=1))
    aut.save()
    logger.debug('(user {pk:%s}) @post_save: author created.' % instance.pk)

