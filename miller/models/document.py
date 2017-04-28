#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shutil,os,codecs, mimetypes, json, requests, tempfile, logging, PyPDF2, bibtexparser

from actstream import action
from actstream.actions import follow

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core import files
from django.core.cache import cache
from django.db import models
from django.db.models.signals import pre_delete, post_save, pre_save
from django.dispatch import receiver, Signal
from django.utils.text import slugify

from miller import helpers
from wand.image import Image, Color


logger = logging.getLogger('miller.commands')

document_ready = Signal(providing_args=["instance", "created"])


def attachment_file_name(instance, filename):
  return os.path.join(instance.type, filename)

def private_attachment_file_name(instance, filename):
  return os.path.join(settings.MEDIA_PRIVATE_ROOT, instance.type, filename)

def snapshot_attachment_file_name(instance, filename):
  print 'generating', os.path.join(instance.type, 'snapshots', filename)
  return os.path.join(instance.type, 'snapshots', filename)


class Document(models.Model):
  BIBLIOGRAPHIC_REFERENCE = 'bibtex'
  CROSSREF_REFERENCE = 'crossref'
  VIDEO_COVER = 'video-cover'
  PICTURE = 'picture'
  IMAGE   = 'image'
  PHOTO   = 'photo'
  VIDEO   = 'video'
  AUDIO   = 'audio'
  TEXT    = 'text'
  PDF     = 'pdf'
  RICH    = 'rich'
  LINK    = 'link'
  AV      = 'audiovisual'
  TYPE_CHOICES = (
    (BIBLIOGRAPHIC_REFERENCE, 'bibtex'),
    (CROSSREF_REFERENCE, 'bibtex'),
    (VIDEO_COVER, 'video interview'),
    (VIDEO, 'video'),
    (TEXT, 'text'),
    (PICTURE, 'picture'),
    (PDF, 'pdf'),
    (IMAGE, 'image'),
    (PHOTO, 'photo'),
    (RICH, 'rich'),
    (LINK, 'link'),
    (AV, 'audiovisual')
  )

  DEFAULT_OEMBED = {
    'provider_name': '',
    'provider_url': '',
    'type': 'rich',
    'title': '',
    'description': '',
    'html': '',
    'details':{}
  }

  type       = models.CharField(max_length=24, choices=TYPE_CHOICES)
  short_url  = models.CharField(max_length=22, db_index=True, default=helpers.create_short_url, unique=True, blank=True)
  
  title      = models.CharField(max_length=500)
  slug       = models.CharField(max_length=150, unique=True, blank=True, db_index=True)

  contents   = models.TextField(null=True, blank=True, default=json.dumps(DEFAULT_OEMBED, indent=1)) # OEMBED (JSON) metadata field, in different languages if available.
  
  data       = JSONField(default=dict)

  copyrights = models.TextField(null=True, blank=True,  default='')

  url        = models.URLField(max_length=500, null=True, blank=True)
  owner      = models.ForeignKey(User); # at least the first author, the one who owns the file.
  attachment = models.FileField(upload_to=attachment_file_name, null=True, blank=True)
  snapshot   = models.FileField(upload_to=snapshot_attachment_file_name, null=True, blank=True)
  mimetype   = models.CharField(max_length=127, blank=True, default='')

  locked     = models.BooleanField(default=False) # prevent accidental override when it is not needed.

  # documents  = models.ManyToManyField("self", through='Mention', symmetrical=False, related_name='mentioned_with')


  @property
  def dmetadata(self):
    if not hasattr(self, '_dmetadata'):
      try:
        self._dmetadata  = json.loads(self.contents)
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
    logger.debug('on document {pk:%s}' %  self.url)
        
    if self.url: 
      logger.debug('url: %s for document {pk:%s}' % (self.url, self.pk))

      try:
        res = requests.get(self.url, timeout=settings.MILLER_URL_REQUEST_TIMEOUT, stream=True)

        if res.status_code == requests.codes.ok:
          self.mimetype = res.headers['content-type'].split(';')[0].lower()
          logger.debug('mimetype found: %s for document {pk:%s}' % (self.mimetype, self.pk))
          if self.mimetype == 'application/pdf':
            # Create a temporary file
            filename = self.url.split('/')[-1]
            filename = filename[:80]
            lf = tempfile.NamedTemporaryFile()


            # Read the streamed image in sections
            for block in res.iter_content(1024 * 8):
              if not block: # If no more file then stop
                break
              lf.write(block) # Write image block to temporary file
            # complete writing.
            lf.flush()

            logger.debug('saving attachment: %s for document {pk:%s}' % (filename, self.pk))
            outfile = os.path.join(settings.MEDIA_PRIVATE_ROOT, self.type, self.short_url)

            try:
              os.makedirs(os.path.dirname(outfile))
            except OSError:
              pass

            
            shutil.copy(lf.name, outfile)
            self.attachment = os.path.join(settings.MEDIA_PRIVATE_RELATIVE_PATH, self.type, self.short_url)
            self.save()
            # clean tempfile
            lf.close()
      
      except requests.exceptions.Timeout:
        logger.debug('url: %s for document {pk:%s} TIMEOUT...' % (self.url, self.pk))
          

  # def generate_metadata(self):
  #   """
  #   deprecated when using JSONField
  #   """

  #   if getattr(self, '__metadata', None) is None:
  #     r = {}
  #     r.update(Document.DEFAULT_OEMBED)
  #     try:
  #       r.update(json.loads(self.contents))
  #     except Exception, e:
  #       logger.exception(e)
  #       r['error'] = '%s'%e
  #     self.__metadata = r
  #     return r
  #   else:
  #     return self.__metadata



  def fill_from_metadata(self):
    if 'error' in self.data: # simply ignore filling from erroneous self.__metadata.
      return
      
    if 'bibtex' in self.data:
      self.data['details'] = self.data['details'] if 'details' in self.data else {}

      try:
        self.data['details']['bibtex'] = bibtexparser.loads(self.data['bibtex']).entries[0]
      except Exception, e:
        logger.exception(e)
        return
      if not self.title and 'title' in self.data['details']['bibtex']:
        self.title = self.data['details']['bibtex']['title']

    # complete self.data section with title
    if not 'title' in self.data or not self.data['title']:
      self.data['title'] = self.title

    # complete with rough reference
    if not 'reference' in self.data or not self.data['reference']:
      self.data['reference'] = self.data['title']



  # dep. brew install ghostscript, brew install imagemagick
  def create_snapshot(self):
    logger.debug('document {pk:%s, mimetype:%s, type:%s} init snapshot' % (self.pk, self.mimetype, self.type))
      
    if self.mimetype and self.attachment and hasattr(self.attachment, 'path'):
      logger.debug('document {pk:%s, mimetype:%s, type:%s} snapshot can be generated' % (self.pk, self.mimetype, self.type))
      
      filename = '%s.snapshot.png' % self.short_url
      outfile = os.path.join(settings.MEDIA_ROOT, snapshot_attachment_file_name(self, filename))

      # generate dir if there is none
      try:
        os.makedirs(os.path.dirname(outfile))
      except OSError:
        logger.debug('document {pk:%s, mimetype:%s, type:%s} creating folder for snapshot' % (self.pk, self.mimetype, self.type))
        pass

      # generate thumbnail
      if self.mimetype == 'image/png' or self.mimetype == 'image/jpeg' or self.mimetype == 'image/gif' or self.type == Document.IMAGE or self.type == Document.PHOTO:
        logger.debug('document {pk:%s, mimetype:%s, type:%s} generating IMAGE thumbnail...' % (self.pk, self.mimetype, self.type))
        
        
        # generate snapshot
        helpers.generate_snapshot(filename=self.attachment.path, output=outfile, width=234)
           
        self.snapshot = snapshot_attachment_file_name(self, filename)#outfile# .save(os.path.basename(outfile), files.images.ImageFile(f), save=False)
        self._dirty = True
        logger.debug('document {pk:%s, mimetype:%s, type:%s} IMAGE thumbnail done.' % (self.pk, self.mimetype, self.type))
        # remove tempfile
        

      # print mimetype
      elif self.mimetype == 'application/pdf':
        logger.debug('document {pk:%s, mimetype:%s, type:%s} generating PDF snapshot...' % (self.pk, self.mimetype, self.type))
        
        pdffile = self.attachment.path
        pdf_im = PyPDF2.PdfFileReader(pdffile)

        # get page
        page = 0
        try:
          metadata = json.loads(self.contents)
          page = int( metadata['thumbnail_page']) if 'thumbnail_page' in metadata else 0
        except Exception as e:
          logger.exception(e)
        
        try:
          # Converting first page into JPG
          with Image(filename='%s[%s]'%(pdffile,page), resolution=150) as img:
            img.format = 'png'
            img.background_color = Color('white') # Set white background.
            img.alpha_channel = 'remove'
            img.save(filename=outfile)

          self.snapshot = snapshot_attachment_file_name(self, filename)#outfile# .save(os.path.basename(outfile), files.images.ImageFile(f), save=False)
          self._dirty = True
        

          # with open(self.attachment.path + '.png') as f:
          #   self.snapshot.save(os.path.basename(self.attachment.path)[:100] + '.png', files.images.ImageFile(f), save=False)
          #   self._dirty = True
          #   logger.debug('document {pk:%s, type:%s} PDF snapshot done.' % (self.pk,self.type))

        except Exception as e:
          logger.exception(e)
          print 'could not save snapshot of the required resource', self.pk
        else:
          logger.debug('snapshot generated for document {pk:%s}, page %s' % (self.pk, page))
    else:
      logger.debug('document {pk:%s} snapshot cannot be generated.' % self.pk)
      

  def noembed(self):
    """
    use noembed MILLER_EMBEDLY_API_KEY to get videos from url
    """
    if self.url:
      logger.debug('document {pk:%s, url:%s} init embedly' % (self.pk, self.url))

      from embedly import Embedly
      
      client = Embedly(settings.MILLER_EMBEDLY_API_KEY)
      embed = client.oembed(self.url, raw=True)
      self.contents = embed['raw'] 
      #  print json.embed
      #else:
      #  logger.warn('document {pk:%s, url:%s} cannot embedly, it is not a recognized provider.' % (self.pk, self.url))


  def create_oembed(self):
    """
    Create a rich oembed for uploaded document, if needed.
    """
    logger.debug('document {pk:%s, mimetype:%s} init oembed' % (self.pk, self.mimetype))
    if self.mimetype == 'application/pdf' and self.attachment and hasattr(self.attachment, 'path'):
      url = '%s%s' %(settings.MILLER_SETTINGS['host'], self.attachment.url)
      self.data['html'] = "<iframe src='https://drive.google.com/viewerng/viewer?url=%s&embedded=true' width='300' height='200' style='border: none;'></iframe>" % url
      self.data['type'] = 'rich'
      self.type = Document.RICH # yep so that client can use the oembed correctly (rich, video, photo, image).
      self._dirty=True
      logger.debug('document {pk:%s} oembed done.' % self.pk)
      
    else:
      logger.debug('document {pk:%s, mimetype:%s} cannot create oembed.' % (self.pk, self.mimetype))
      

  def save(self, *args, **kwargs):
    """
    Override ortodox save method. Check for duplicates on OPTIONAL fields (url in this case)
    """
    if not hasattr(self, '_saved'):
      self._saved = 1
    else:
      self._saved = self._saved + 1
    logger.debug('document {pk:%s} init save, time=%s' % (self.pk, self._saved))
    
    if not self.pk:
      # get the missing fields from metadata bibtex if any.
      self.fill_from_metadata()
      
      if self.url:
        print 'verify the url:', self.url
        try:
          doc = Document.objects.get(url=self.url)
          
          self.pk          = doc.pk
          self.title       = doc.title
          self.slug        = doc.slug
          self.type        = doc.type
          self.short_url   = doc.short_url
          self.copyrights  = doc.copyrights
          self.url         = doc.url
          self.owner       = doc.owner
          self.attachment  = doc.attachment
          self.snapshot    = doc.snapshot
          self.mimetype    = doc.mimetype

          # update contents only
          if not doc.locked and self.contents != doc.contents:
            # print "updating the content", self.contents, doc.contents
            super(Document, self).save(force_update=True, update_fields=['contents'])
            # print "done, now:", self.contents
          else:
            # print "do not update the content"
            self.contents = doc.contents
        except Document.DoesNotExist:
          logger.debug('document {pk:%s,url:%s} from url' % (self.pk, self.url[:10]))
          super(Document, self).save(*args, **kwargs)
          action.send(self.owner, verb='created', target=self)
          
      else:
        super(Document, self).save(*args, **kwargs)
        action.send(self.owner, verb='created', target=self)
       
    else:
      super(Document, self).save(*args, **kwargs)


@receiver(pre_save, sender=Document)
def complete_instance(sender, instance, **kwargs):
  logger.debug('document {pk:%s} @pre_save' % instance.pk)
  if not instance.slug:
    instance.slug = helpers.get_unique_slug(instance, instance.title, max_length=68)
    logger.debug('document {pk:%s, slug:%s} @pre_save slug generated' % (instance.pk, instance.slug))



@receiver(post_save, sender=Document)
def dispatcher(sender, instance, created, **kwargs):
  """
  Generic post_save handler. Dispatch a document_ready signal.
  If receiver need to update the instance, they just need to put the property `_dirty`
  """
  if getattr(instance, '_dispatched', None) is None:
    instance._dispatched = True
  else:
    logger.debug('document@post_save  {pk:%s} dispatching already dispatched. Skipping.' % instance.pk)
    # done already.
    return
  
  logger.debug('document@post_save  {pk:%s} dispatching @document_ready...' % instance.pk)
  
  document_ready.send(sender=sender, instance=instance, created=created)
  
  if getattr(instance, '_dirty', None) is not None:
    logger.debug('document@post_save  {pk:%s} dirty instance. Need to call instance.save()..' % instance.pk)
    instance.save()
  else:
    logger.debug('document@post_save  {pk:%s} no need to save the instance again.' % instance.pk)
  if created:  
    follow(instance.owner, instance)


# store in whoosh
@receiver(document_ready, sender=Document)
def store_working_md(sender, instance, created, **kwargs):
  logger.debug('document@document_ready {pk:%s}: storing in whoosh' % instance.pk)
  instance.store()


@receiver(document_ready, sender=Document)
def create_snapshot(sender, instance, created, **kwargs):
  if created and instance.attachment and hasattr(instance.attachment, 'path'):
    logger.debug('document@document_ready {pk:%s} need to create snapshot' % instance.pk)
    instance.create_snapshot()
  else:
    logger.debug('document@document_ready {pk:%s} NO need to create snapshot.' % instance.pk)


@receiver(document_ready, sender=Document)
def create_oembed(sender, instance, created, **kwargs):
  if created:
    try:
      logger.debug('document@document_ready {pk:%s}: need to create oembed' % instance.pk)
      instance.create_oembed()
    except Exception as e:
      logger.exception(e)
  else:
    logger.debug('document@document_ready {pk:%s}: NO need to create oembed.' % instance.pk)


@receiver(document_ready, sender=Document)
def clean_related_documents_cache(sender, instance, created, **kwargs):
  # list of affected stories
  affected = set(list(instance.stories.values_list('short_url', flat=True)) + list(instance.stories.values_list('short_url', flat=True)))
  
  for key in affected:
    ckey = 'story.%s' % key
    cache.delete(ckey)

  logger.debug('document@document_ready {pk:%s}: clean cache of %s related docs.' % (instance.pk, len(affected)))


