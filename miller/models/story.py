#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pypandoc, re, os, codecs, json, logging
import django.dispatch

from BeautifulSoup import BeautifulSoup

from django.conf import settings
from django.core.signals import request_finished
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.text import slugify

from jsonfield import JSONField

from markdown import markdown

from miller import helpers
from miller.models import Tag, Document

from simplemde.fields import SimpleMDEField



logger = logging.getLogger('miller')

story_ready = django.dispatch.Signal(providing_args=["instance", "created"])

def user_path(instance, filename):
  root, ext = os.path.splitext(filename)
  src = os.path.join(settings.MEDIA_ROOT, instance.owner.profile.short_url, instance.short_url + ext)
  return src


class Story(models.Model):

  
  DRAFT   = 'draft' # visible just for you
  SHARED  = 'shared' # share with specific user
  PUBLIC  = 'public' # everyone can access that.
  EDITING = 'editing' # only staff and editors access this
  REVIEW  = 'review' # staff, editors and reviewer acces this
  

  STATUS_CHOICES = (
    (DRAFT,   'draft'),
    (SHARED,  'shared'),
    (PUBLIC,  'public'), # accepted paper.
    (EDITING, 'editing'),
    (REVIEW,  'review'), # ask for review
  )

  short_url = models.CharField(max_length=22, db_index=True, default=helpers.create_short_url, unique=True)
  
  title     = models.CharField(max_length=500)
  slug      = models.CharField(max_length=140, unique=True, blank=True) # force the unicity of the slug (story lookup from the short_url)
  abstract  = models.CharField(max_length=500, blank=True, null=True)
  contents  = SimpleMDEField(verbose_name=u'mardown content',default='',blank=True) # It will store the last markdown contents.
  metadata  = JSONField(default=json.dumps({'title':{'en':'', 'fr':''}, 'abstract':{'en':'', 'fr':''}})) # it will contain, JSON fashion


  date               = models.DateTimeField(blank=True, null=True) # date displayed (metadata)
  date_created       = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  status    = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)

  owner     = models.ForeignKey(User); # at least the first author, the one who owns the file.
  authors   = models.ManyToManyField(User, related_name='authors', blank=True) # collaborators
  watchers  = models.ManyToManyField(User, related_name='watchers', blank=True) # collaborators
  documents = models.ManyToManyField(Document, related_name='documents', through='Caption', blank=True)
  
  # the leading document(s), e.g. an interview
  covers = models.ManyToManyField(Document, related_name='covers', blank=True)

  tags      = models.ManyToManyField(Tag, blank=True) # tags

  # cover thumbnail, e.g. http://www.eleganzadelgusto.com/wordpress/wp-content/uploads/2014/05/Marcello-Mastroianni-for-Arturo-Zavattini.jpg
  cover = models.URLField(max_length=500, blank=True, null=True)

  # cover copyright or caption, markdown flavoured. If any
  cover_copyright = models.CharField(max_length=140, blank=True, null=True)

  # fileField
  source = models.FileField(upload_to=user_path, blank=True, null=True)

  # fileField (usually a zotero-friendly importable file)
  bibliography = models.FileField(upload_to=user_path, blank=True, null=True)

  # set the plural name and fix the default sorting order
  class Meta:
    ordering = ('-date_last_modified',)
    verbose_name_plural = 'stories'

  
  # get story path based on random generated shorten url
  def get_path(self):
    return os.path.join(self.owner.profile.get_path(), self.short_url+ '.md')
  
  def get_absolute_url(self):
    return u"/#!/story/%s/" % self.slug

  def __unicode__(self):
    return '%s - by %s' % (self.title, self.owner.username)

  # store into the whoosh index
  def store(self, ix=None):
    if settings.TESTING:
      logger.debug('mock storing data during test')
      return

    if ix is None:
      ix = helpers.get_whoosh_index()
    writer = ix.writer()
    writer.update_document(
      title = self.title,
      path = u"%s"%self.short_url,
      content =  u"\n".join(BeautifulSoup(markdown(u"\n".join(filter(None,[self.title, self.abstract, self.contents])), extensions=['footnotes'])).findAll(text=True)),
      tags = u",".join([u'%s'%t.name for t in self.tags.all()]),
      classname = u"story")
    writer.commit()


  # unstore (usually when deleted)
  def unstore(self, ix=None):
    # if settings.TESTING:
    #   logger.debug('mock storing data during test')
    #   return
    if ix is None:
      ix = helpers.get_whoosh_index()
    
    writer = ix.writer()

    writer.delete_by_term('path', u"%s"%self.short_url)
    # Save the deletion to disk
    writer.commit()


  # convert the content of in a suitable markdown file. to be used before store() and before create_working_md() are called
  # if force is true, it overrides the contents field.
  def convert(self, force=False):
    
    # we force to use # headers by setting the threshold of 3 so that h1 "===" is transformed to h3 "###"
    contents = pypandoc.convert_file(self.source.path, 'markdown',  extra_args=['--base-header-level=3'])
    # ... but we have to transform them back, minus a level (e.g. transformed h1 becomes h2).
    # We should check if we can use the pandoc options for that directly
    self.contents = re.sub(r'#(#+)', r'\1', contents) 


  # convert the last saved content (markdown file) to a specific format (default: docx)
  # the media will be in the user MEDIA folder...
  def download(self, outputFormat='docx', language=None, extension=None):
    outputfile = user_path(self, '%s.%s' % (self.short_url, extension if extension is not None else outputFormat))
    tempoutputfile = user_path(self, '__%s.md' % self.short_url)

    with codecs.open(tempoutputfile, "w", "utf-8") as temp:
      temp.write(u'\n\n'.join([
        u"#%s" % self.title,
        u"> %s" % self.abstract if self.abstract else "",
        # generate citation
        self.contents
      ]))

    # reverted = re.sub(r'#(#+)', r'\1', contents) 
    pypandoc.convert_file(tempoutputfile, outputFormat, outputfile=outputfile, extra_args=['--base-header-level=1'])
    os.remove(tempoutputfile)

    return outputfile


  # save hook
  def save(self, *args, **kwargs):
    if not self.id and not self.slug:
      slug = slugify(self.title)
      slug_exists = True
      counter = 1
      self.slug = slug
      while slug_exists:
        try:
          slug_exits = Story.objects.get(slug=slug)
          if slug_exits:
              slug = self.slug + '-' + str(counter)
              counter += 1
        except Story.DoesNotExist:
          self.slug = slug
          break

    if not hasattr(self, 'filling_metadata'):
      self.filling_metadata = True
      
      try:
        metadata = self.metadata if type(self.metadata) is dict else json.loads(self.metadata)
        
        if 'title' not in metadata:
          metadata['title'] = {}
        if 'abstract' not in metadata:
          metadata['abstract'] = {}

        for default_language_code, label, language_code in settings.LANGUAGES:
          logger.debug('metadata filling lang:%s' % language_code)
          if language_code not in metadata['title']:
            metadata['title'][language_code] = self.title

          if language_code not in metadata['abstract']:
            metadata['abstract'][language_code] = self.abstract

        logger.debug('metadata filled.')
        self.metadata = json.dumps(metadata)
      except Exception as e:
        logger.exception(e)




    # transform automatically text in ontents if contents is empty

    # if bool(self.source):
    #   print "))))))need conversion"
    #   self.convert()
    
    super(Story, self).save(*args, **kwargs)


# generic story_ready handlers ;) store in whoosh
@receiver(post_save, sender=Story)
def dispatcher(sender, instance, created, **kwargs):
  if not hasattr(instance, '__dispatcher'):
    instance.__dispatcher = True
  else:
    return
  # dispatch (call). 
  logger.debug('(story {pk:%s}) dispatch @story_ready' % instance.pk)
  story_ready.send(sender=sender, instance=instance, created=created)
  
  if hasattr(instance, '__dirty'):
    instance.save()
    logger.debug('(story {pk:%s}) saved.' % instance.pk)
  


# store in whoosh
@receiver(story_ready, sender=Story)
def store_working_md(sender, instance, created, **kwargs):
  instance.store()
  logger.debug('(story {pk:%s}) @story_ready store_working_md: done' % instance.pk)


# clean store in whoosh when deleted
@receiver(pre_delete, sender=Story)
def unstore_working_md(sender, instance, **kwargs):
  instance.unstore()
  logger.debug('(story {pk:%s}) @pre_delete unstore_working_md: done' % instance.pk)




# check if there is a source file of type docx attached and transform it to content.
@receiver(story_ready, sender=Story)
def transform_source(sender, instance, created, **kwargs):
  # print 'story is created?', instance.pk, created
  if not created:
    return
  if bool(instance.source):
    logger.debug('(story {pk:%s}) @story_ready transform_source: converting...' % instance.pk)
    instance.convert()
    instance.__dirty = True
  else:
    logger.debug('(story {pk:%s}) @story_ready transform_source: skipping.' % instance.pk)
  
  
  logger.debug('(story {pk:%s}) @story_ready transform_source: done' % instance.pk)
  



@receiver(story_ready, sender=Story)
def create_first_author(sender, instance, created, **kwargs):
  if created:
    instance.authors.add(instance.owner)
    instance.__dirty = True
    logger.debug('(story {pk:%s}) @story_ready: {username:%s}" done.' % (instance.pk, instance.owner.username))


# create story file if it is not exists; if the story eists already, cfr the followinf story_ready
@receiver(story_ready, sender=Story)
def create_working_md(sender, instance, created, **kwargs):
  logger.debug('(story {pk:%s}) @story_ready: git...' % instance.pk)
  
  path = instance.get_path()
  
  f = codecs.open(path, encoding='utf-8', mode='w+')
  f.write(instance.contents)
  f.seek(0)
  f.close()

  from git import Repo, Commit, Actor, Tree

  author = Actor(instance.owner.username, instance.owner.email)
  committer = Actor(settings.GIT_COMMITTER['name'], settings.GIT_COMMITTER['email'])

  # commit if there are any differences
  repo = Repo.init(settings.GIT_ROOT)

  # add and commit JUST THIS FILE
  #tree = Tree(repo=repo, path=instance.owner.profile.get_path())
  repo.index.add([instance.owner.profile.get_path()])
  repo.index.commit(message=u"saving %s" % instance.title, author=author, committer=committer)
  logger.debug('(story {pk:%s}) @story_ready: done.' % instance.pk)



# clean makdown version and commit
@receiver(pre_delete, sender=Story)
def delete_working_md(sender, instance, **kwargs):
  logger.debug('(story {pk:%s}) @pre_delete: %s' % (instance.pk, instance.get_path()))
  
  path = instance.get_path()
  

  from git import Repo, Commit, Actor, Tree

  author = Actor(instance.owner.username, instance.owner.email)
  committer = Actor(settings.GIT_COMMITTER['name'], settings.GIT_COMMITTER['email'])

  # /* delete file */
  os.remove(path);
  # keep exports in .gitignore

  logger.debug('(story {pk:%s}) @story_ready: markdown removed.' % instance.pk)

  # commit if there are any differences
  repo = Repo.init(settings.GIT_ROOT)

  # add and commit JUST THIS FILE
  #tree = Tree(repo=repo, path=instance.owner.profile.get_path())
  repo.git.add(update=True)
  repo.index.commit(message=u"deleting %s" % instance.title, author=author, committer=committer)


  logger.debug('(story {pk:%s}) @story_ready: done.' % instance.pk)

