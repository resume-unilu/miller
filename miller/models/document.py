#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs, mimetypes, json, requests, tempfile

from django.conf import settings
from django.contrib.auth.models import User
from django.core import files
from django.db import models
from django.db.models.signals import pre_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from miller import helpers



def attachment_file_name(instance, filename):
  return os.path.join(instance.type, filename)

def snapshot_attachment_file_name(instance, filename):
  return os.path.join(instance.type, 'snapshots', filename)


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
    ("image", 'image'),
    ("photo", 'photo'),
    (RICH, 'rich'),
    (LINK, 'link'),
    (AV, 'audiovisual')
  )

  type       = models.CharField(max_length=24, choices=TYPE_CHOICES)
  short_url  = models.CharField(max_length=22, db_index=True, default=helpers.create_short_url, unique=True, blank=True)
  
  title      = models.CharField(max_length=500)
  slug       = models.CharField(max_length=150, unique=True, blank=True)

  contents   = models.TextField(null=True, blank=True, default=json.dumps({
    'provider_name': '',
    'provider_url': '',
    'type': 'rich',
    'title': '',
    'description': '',
    'html': '',
    'details':{}
  })) # OEMBED (JSON) metadata field, in different languages if available.
  
  copyrights = models.TextField(null=True, blank=True,  default='')

  url        = models.URLField(max_length=500, null=True, blank=True)
  owner      = models.ForeignKey(User); # at least the first author, the one who owns the file.
  attachment = models.FileField(upload_to=attachment_file_name, null=True, blank=True)
  snapshot   = models.FileField(upload_to=snapshot_attachment_file_name, null=True, blank=True)
  mimetype   = models.CharField(max_length=127, blank=True, default='')

  models.URLField(null=True, blank=True)

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


  # download remote pdfs allowing to produce snapshots. This should be followed by save() :)
  def fill_from_url(self):
    if not self.mimetype and self.url: 
      res = requests.get(self.url,  timeout=5, stream=True)
      if res.status_code == requests.codes.ok:
        self.mimetype = res.headers['content-type']
        
        if self.mimetype == 'application/pdf':
          # Create a temporary file
          filename = self.url.split('/')[-1]
          
          lf = tempfile.NamedTemporaryFile()

          # Read the streamed image in sections
          for block in res.iter_content(1024 * 8):
            if not block: # If no more file then stop
              break
            lf.write(block) # Write image block to temporary file
            

          self.attachment.save(filename, files.File(lf))


  # dep. brew install ghostscript, brew install imagemagick
  def create_snapshot(self):
    if self.attachment and hasattr(self.attachment, 'path'):
      
      mimetype = mimetypes.MimeTypes().guess_type(self.attachment.path)[0]
      # print mimetype
      if mimetype == 'application/pdf':
        import PyPDF2
        pdf_im = PyPDF2.PdfFileReader(self.attachment)
        from wand.image import Image
        try:
          # Converting first page into JPG
          with Image(filename=self.attachment.path + '[0]', resolution=150) as img:
            img.save(filename=self.attachment.path + '.png')
            snapshot = self.attachment.url + '.png'
            Document.objects.filter(pk=self.pk).update(snapshot=snapshot)
        except Exception:
          pass
          print 'could not save snapshot of the required resource', self.id

  def save(self, *args, **kwargs):
    if not self.id and self.url:
      print 'CHECK THE ID', self.url
      try:
        doc = Document.objects.get(url=self.url)
        print 'CHECK THE ID', doc.pk
        self.pk = doc.pk
      except Document.DoesNotExist:
        pass
    super(Document, self).save(*args, **kwargs)



# store in whoosh
@receiver(post_save, sender=Document)
def store_working_md(sender, instance, created, **kwargs):
  instance.store()


@receiver(pre_save, sender=Document)
def create_slug(sender, instance, **kwargs):
  if not instance.id and not instance.slug:
    slug = slugify(instance.title)
    slug_exists = True
    counter = 1
    instance.slug = slug
    while slug_exists:
      try:
        slug_exits = Document.objects.get(slug=slug)
        if slug_exits:
            slug = instance.slug + '-' + str(counter)
            counter += 1
      except Document.DoesNotExist:
        instance.slug = slug
        break


