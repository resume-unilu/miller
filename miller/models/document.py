#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs, mimetypes

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from miller import helpers


def attachment_file_name(instance, filename):
  return os.path.join(instance.type, filename)


class Document(models.Model):
  BIBLIOGRAPHIC_REFERENCE = 'bibtex'
  VIDEO_COVER = 'video-cover'
  PICTURE = 'picture'
  VIDEO   = 'video'
  AUDIO   = 'audio'
  PDF     = 'pdf'

  TYPE_CHOICES = (
    (BIBLIOGRAPHIC_REFERENCE, 'bibtex'),
    (VIDEO_COVER, 'video interview'),
    (VIDEO, 'video'),
    (PICTURE, 'picture'),
    (PDF, 'pdf'),
  )

  type       = models.CharField(max_length=24, choices=TYPE_CHOICES)
  short_url  = models.CharField(max_length=22, default=helpers.create_short_url, unique=True)
  
  title      = models.CharField(max_length=500)
  slug       = models.CharField(max_length=100, unique=True)

  contents   = models.TextField(null=True, blank=True, default='') # OEMBED or markdown flavoured metadata field, in different languages if available.
  copyrights = models.TextField(null=True, blank=True,  default='')

  url        = models.URLField(max_length=500, null=True, blank=True)
  owner      = models.ForeignKey(User); # at least the first author, the one who owns the file.
  attachment = models.FileField(upload_to=attachment_file_name, null=True, blank=True)
  snapshot   = models.URLField(null=True, blank=True)


  def __unicode__(self):
    return '%s (%s)' % (self.slug, self.type)

# dep. brew install ghostscript, brew install imagemagick
@receiver(post_save, sender=Document)
def create_snapshot(sender, instance, created, **kwargs):
  if instance.attachment and hasattr(instance.attachment, 'path'):
    import mimetypes
    mimetype = mimetypes.MimeTypes().guess_type(instance.attachment.path)[0]
    print mimetype
    if mimetype == 'application/pdf':
      import PyPDF2
      pdf_im = PyPDF2.PdfFileReader(instance.attachment)
      from wand.image import Image
      try:
        # Converting first page into JPG
        with Image(filename=instance.attachment.path + '[0]', resolution=150) as img:
          img.save(filename=instance.attachment.path + '.png')
          snapshot = instance.attachment.url + '.png'
          Document.objects.filter(pk=instance.pk).update(snapshot=snapshot)
      except Exception:
        print 'could not save snapshot of the required resource', instance.id

# automatically fill metadata if contents field is empty
@receiver(post_save, sender=Document)
def fill_contents(sender, instance, created, **kwargs):
  pass





