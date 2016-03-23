#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from miller import helpers

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User



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


  class Meta:
    app_label="miller"


  # get profile path based on random generated shorten url
  def get_path(self):
    return os.path.join(settings.PROFILE_PATH_ROOT, self.short_url)


# Create a folder to store user contents: stories, files etc..
@receiver(post_save, sender=User)
def create_working_folder(sender, instance, created, **kwargs):
  if created:
    pro = Profile(user=instance)
    pro.save()
    path = pro.get_path()
    if not os.path.exists(path):
      os.makedirs(path)



@receiver(pre_delete, sender=User)
def delete_working_folder(sender, instance, **kwargs):
  '''
  delete user working_folder. Are you sure?
  '''
  #path = instance.get_path()
  #shutil.rmtree(path)
  pass