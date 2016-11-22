#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, logging, shutil

from actstream import action

from miller import helpers

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User



logger = logging.getLogger('miller')
# Create a Profile object, connected with the user.
# THe picture is given as a remote url.
# Cfr. admin.py
class Profile(models.Model):
  user          = models.OneToOneField(User, on_delete=models.CASCADE)
  
  short_url     = models.CharField(max_length=22, default=helpers.create_short_url, unique=True)
  
  bio           = models.TextField(null=True, blank=True) # markdown here
  picture       = models.URLField(max_length=160, blank=True, null=True)

  date_created       = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  def __unicode__(self):
    return self.user.username

  class Meta:
    app_label="miller"


  # get profile path UNDER GIT based on random generated shorten url. This does not apply for user uploaded contents.
  def get_path(self):
    return os.path.join(settings.PROFILE_PATH_ROOT, self.short_url)


# Create a folder to store user contents: stories, files etc..
@receiver(post_save, sender=User)
def create_working_folder(sender, instance, created, **kwargs):
  if created:
    pro = Profile(user=instance)
    pro.save()
    logger.debug('(user {pk:%s}) @post_save: done.' % instance.pk)
    action.send(pro.user, verb='created', target=pro)



@receiver(post_save, sender=Profile)
def check_working_folder(sender, instance, created, **kwargs):
  user_path = os.path.join(settings.MEDIA_ROOT, instance.short_url)
  path = instance.get_path()

  if not os.path.exists(path):
    os.makedirs(path)
  if not os.path.exists(user_path):
    os.makedirs(user_path)

  logger.debug('(profile {pk:%s}) @post_save: done.' % instance.pk)


@receiver(post_save, sender=Profile)
def create_zotero_collection(sender, instance, created, **kwargs):
  if not hasattr(settings, 'ZOTERO_IDENTITY'):
    logger.warn('(profile {pk:%s}) @post_save: ZOTERO_IDENTITY not set, skipping...' % instance.pk)
    return
  created, collection, zotero = helpers.get_or_create_zotero_collection(instance.user.username)
  if collection is not None:
    logger.debug('(profile {pk:%s}) @post_save: done.' % instance.pk)
  else:
    logger.warn('(profile {pk:%s}) @post_save: failed!' % instance.pk)


@receiver(pre_delete, sender=Profile)
def delete_working_folder(sender, instance, **kwargs):
  '''
  delete user working_folder. Are you sure?
  '''
  path = instance.get_path()
  shutil.rmtree(path)
  logger.debug('(profile {pk:%s}) @pre_delete: done.' % instance.pk)


# delete the user media folder, created once an user upload a file or download it
@receiver(pre_delete, sender=Profile)
def delete_user_media_folder(sender, instance, **kwargs):
  path = os.path.join(settings.MEDIA_ROOT, instance.short_url)
  shutil.rmtree(path)
  logger.debug('(profile {pk:%s}) @pre_delete: done.' % instance.pk)
