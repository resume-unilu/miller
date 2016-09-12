#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs, mimetypes, json

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
  TEXT    = 'text'
  PDF     = 'pdf'
  RICH    = 'rich'
  LINK    = 'link'
  AV      = 'audiovisual'
  TYPE_CHOICES = (
    (BIBLIOGRAPHIC_REFERENCE, 'bibtex'),
    (VIDEO_COVER, 'video interview'),
    (VIDEO, 'video'),
    (TEXT, 'text'),
    (PICTURE, 'picture'),
    (PDF, 'pdf'),
    ("image", 'picture'),
    ("photo", 'picture'),
    (RICH, 'rich'),
    (LINK, 'link'),
    (AV, 'audiovisual')
  )

  type       = models.CharField(max_length=24, choices=TYPE_CHOICES)
  short_url  = models.CharField(max_length=22, db_index=True, default=helpers.create_short_url, unique=True)
  
  title      = models.CharField(max_length=500)
  slug       = models.CharField(max_length=150, unique=True)

  contents   = models.TextField(null=True, blank=True, default='') # OEMBED or markdown flavoured metadata field, in different languages if available.
  copyrights = models.TextField(null=True, blank=True,  default='')

  url        = models.URLField(max_length=500, null=True, blank=True)
  owner      = models.ForeignKey(User); # at least the first author, the one who owns the file.
  attachment = models.FileField(upload_to=attachment_file_name, null=True, blank=True)
  snapshot   = models.URLField(null=True, blank=True)

  class Meta:
    ordering = ['-id']

  def __unicode__(self):
    return '%s (%s)' % (self.slug, self.type)

  # store into the whoosh index
  def store(self, ix=None):
    if ix is None:
      ix = helpers.get_whoosh_index()
    writer = ix.writer()

    try:
      _metadata = json.loads(self.contents)

      metadata = u"\n".join(filter(None, [
        _metadata.get('author_name'),
        u"\n".join(filter(None, [
          _metadata['details']['title'].get('en'), 
          _metadata['details']['title'].get('fr')
        ])) if 'details' in _metadata and 'title' in _metadata['details'] else _metadata.get('title'),
        _metadata.get('description'),
        u"\n".join(filter(None, [
          _metadata['details']['caption'].get('en'),
          _metadata['details']['caption'].get('fr')
        ])) if 'details' in _metadata and 'caption' in _metadata['details'] else _metadata.get('caption')
      ]))
    except TypeError:
      metadata = self.title
    except ValueError:
      metadata = self.title

    content = u"\n".join(filter(None, [metadata, self.url]))
    
    writer.update_document(
      title = self.title,
      path = u"%s"% self.short_url,
      content =  content,
      classname = u"document")
    writer.commit()


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

# store in whoosh
@receiver(post_save, sender=Document)
def store_working_md(sender, instance, created, **kwargs):
  instance.store()




