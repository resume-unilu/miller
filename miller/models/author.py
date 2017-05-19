#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, json

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from miller import helpers
from miller.models import Profile

logger = logging.getLogger('miller')


class Author(models.Model):
  fullname    = models.TextField()
  affiliation = models.TextField(null=True, blank=True) # e.g Government and Politics, University of Luxembpourg
  metadata    = models.TextField(null=True, blank=True, default=json.dumps({
    'firstname': '',
    'lastname': ''
  }, indent=1))
  data        = JSONField(default=dict)
  slug        = models.CharField(max_length=140, unique=True, blank=True)
  user        = models.ForeignKey(User, related_name='authorship', blank=True, null=True, on_delete=models.CASCADE)

  @property
  def dmetadata(self):
    if not hasattr(self, '_dmetadata'):
      try:
        self._dmetadata  = json.loads(self.metadata)
      except Exception as e:
        self._dmetadata = {}
        logger.exception(e)
        return {}
      else:
        return self._dmetadata
      instance._dispatcher = True
    else:
      return self._dmetadata


  class Meta:
    app_label="miller"

  def __unicode__(self):
    return u' '.join(filter(None,[
      self.fullname, 
      '(%s)'%self.user.username if self.user else None,
      self.affiliation
    ]))

  def save(self, *args, **kwargs):
    if not self.pk and not self.slug:
      self.slug = helpers.get_unique_slug(self, self.fullname)
    super(Author, self).save(*args, **kwargs)


  def updatePublishedStories(self):
    num_stories = self.stories.filter(status='public').count()
    self.data.update({
      'num_stories': num_stories
    })
    self.save()

# create an author whenever a Profile is created.
@receiver(post_save, sender=Profile)
def create_author(sender, instance, created, **kwargs):
  if kwargs['raw']:
    return
  if created:
    fullname = u'%s %s' % (instance.user.first_name, instance.user.last_name) if instance.user.first_name else instance.user.username
    aut = Author(user=instance.user, fullname=fullname, data={
      'firstname': instance.user.first_name,
      'lastname': instance.user.last_name
    }, indent=1)
    aut.save()
    logger.debug('(user {pk:%s}) @post_save: author created.' % instance.pk)

