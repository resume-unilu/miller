#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, logging
from actstream import action

from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from miller import helpers

logger = logging.getLogger('miller.commands')

class Comment(models.Model):
  """
  Stores a single comment on a writing item (article, news etc..); this model is related to :model:`miller.Story` and
  :model:`auth.User`. All edits can be done by the owner or by the staff.
  """
  PENDING  = 'pending' # visible just for you
  PUBLIC   = 'public' # everyone can see this.
  PRIVATE  = 'private' # only staff, story authors and comment owner can see this
  ONREVIEW = 'on review' # only staff, story authors and comment owner can see this
  DELETED  = 'deleted'

  STATUS_CHOICES = (
    (PENDING,   'pending acceptation'),
    (PRIVATE,  'accepted, privately visible'),
    (ONREVIEW, 'from reviewer'),
    (PUBLIC,  'accepted, publicly visible'), # accepted paper.
    (DELETED, 'deleted'), # deleted comments, marked to be removed forever.
  )

  short_url = models.CharField(max_length=22, db_index=True, default=helpers.create_short_url, unique=True)
  
  story = models.ForeignKey('miller.Story', related_name='comments')
  owner = models.ForeignKey('auth.User'); # at least the first author, the one who owns the file.
  
  # follows = model.foreignKey(self);
  status    = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING, db_index=True)

  date               = models.DateTimeField(null=True, blank=True, auto_now_add=True, db_index=True) # date displayed (metadata)
  date_created       = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  # according to annotation data model http://www.openannotation.org/spec/core/
  contents = models.TextField(default=json.dumps({
    'title': '',
    'content': '',
    'annotation': {}
  }, indent=1),blank=True)

  # highlights rangy identifiers, given as text (e.g. path)
  highlights = models.CharField(default='', blank=True, max_length=100)


@receiver(pre_save, sender=Comment)
def complete_instance(sender, instance, **kwargs):
  """
  Substitute the instance.highlights identifier with the correct one.
  Highlights are generated story property highlights
  """
  logger.debug('comment {pk:%s} @pre_save' % instance.pk)
  if instance.highlights:
    instance.highlights = instance.highlights.replace('$highlight$', '$%s$' % instance.short_url)



@receiver(post_save, sender=Comment)
def just_commented(sender, instance, created, **kwargs):
  """
  Every time someone comment on a story item, an action is saved
  """
  logger.debug('comment {pk:%s, short_url:%s} @post_save' % (instance.pk, instance.short_url))
  if created:  
    try:
      action.send(instance.owner, verb='commented', target=instance.story)
      logger.debug('comment {pk:%s, short_url:%s} @post_save action saved.' % (instance.pk, instance.short_url))
  
    except Exception as e:
      logger.exception(e)
  