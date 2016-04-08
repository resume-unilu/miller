#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from miller import helpers


def attachment_file_name(instance, filename):
  return os.path.join(instance.type, filename)


class Document(models.Model):
  BIBLIOGRAPHIC_REFERENCE = 'bibtex'
  PICTURE = 'picture'
  VIDEO   = 'video'
  AUDIO   = 'audio'

  TYPE_CHOICES = (
    (BIBLIOGRAPHIC_REFERENCE, 'bibtex'),
    (VIDEO, 'video'),
    (PICTURE, 'picture'),
  )

  type       = models.CharField(max_length=24, choices=TYPE_CHOICES)
  short_url  = models.CharField(max_length=22, default=helpers.create_short_url, unique=True)
  
  title      = models.CharField(max_length=500)
  slug       = models.CharField(max_length=100, unique=True)

  contents   = models.TextField() # markdown flavoured metadata field, in different languages if available.
  copyrights = models.TextField()

  url        = models.URLField(max_length=500, null=True, blank=True)
  owner      = models.ForeignKey(User); # at least the first author, the one who owns the file.
  attachment = models.FileField(upload_to=attachment_file_name)

  def __unicode__(self):
    return '%s (%s)' % (self.slug, self.type)
