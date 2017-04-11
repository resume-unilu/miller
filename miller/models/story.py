#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pypandoc, re, os, codecs, json, logging, errno
import django.dispatch

from actstream import action
from actstream.actions import follow

from BeautifulSoup import BeautifulSoup

from django.conf import settings
from django.core.signals import request_finished
from django.core.cache import cache
from django.db import models
from django.db.models.signals import pre_delete, post_save, m2m_changed, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.text import slugify

# from jsonfield import JSONField
from git import Repo, Commit, Actor, Tree

from markdown import markdown

from miller import helpers
from miller.models import Tag, Document, Author

# from simplemde.fields import SimpleMDEField
from templated_email import send_templated_mail
      


logger = logging.getLogger('miller.commands')

story_ready = django.dispatch.Signal(providing_args=["instance", "created"])

def user_path(instance, filename, safeOrigin=False):
  root, ext = os.path.splitext(filename)
  src = os.path.join(settings.MEDIA_ROOT, instance.owner.profile.short_url if not settings.TESTING else 'test_%s' % instance.owner.username, instance.short_url + ext if not safeOrigin else filename)
  return src



class Story(models.Model):
  language_dict = helpers.get_languages_dict()
  
  DRAFT    = 'draft'   # visible just for you and staff users
  SHARED   = 'shared'  # share with specific user
  PUBLIC   = 'public'  # everyone can access that.
  # status related to review process.
  PENDING      = 'pending'
  EDITING      = 'editing' # only staff and editors access this
  REVIEW       = 'review'  # staff, editors and reviewer acces this
  REVIEW_DONE  = 'reviewdone'

  DELETED  = 'deleted' # will be sent to the bin
  # REFUSED  = 'refused' # will be sent to the bin

  STATUS_CHOICES = (
    (DRAFT,   'draft'),
    (SHARED,  'shared'),
    (PUBLIC,  'public'),  # accepted paper.
    (DELETED, 'deleted'),

    (PENDING,     'pending review'),  # ask for publication, pending review
    (EDITING,     'editing'), # ask for editing review
    (REVIEW,      'review'),             # under review
    (REVIEW_DONE, 'review done')
  )

  short_url = models.CharField(max_length=22, db_index=True, default=helpers.create_short_url, unique=True)
  
  title     = models.CharField(max_length=500)
  slug      = models.CharField(max_length=140, unique=True, blank=True, db_index=True) # force the unicity of the slug (story lookup from the short_url)
  abstract  = models.CharField(max_length=2000, blank=True, null=True)
  contents  = models.TextField(verbose_name=u'mardown content',default='',blank=True) # It will store the last markdown contents.
  metadata  = models.TextField(default=json.dumps({
    'title': language_dict,
    'abstract':language_dict
  }, indent=1),blank=True) # it will contain, JSON fashion


  date               = models.DateTimeField(null=True, blank=True, db_index=True) # date displayed (metadata)
  date_created       = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  status    = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT, db_index=True)
  priority  = models.PositiveIntegerField(default=0, db_index=True)

  owner     = models.ForeignKey(User); # at least the first author, the one who owns the file.
  
  authors   = models.ManyToManyField(Author, related_name='stories', blank=True) # collaborators
  documents = models.ManyToManyField(Document, related_name='documents', through='Caption', blank=True)

  stories   = models.ManyToManyField("self", through='Mention', symmetrical=False, related_name='mentioned_to')

  # 1.x versions for DRAFT mode
  # 2.x versions for EDITING mode
  # 2.0 once version has been REVIEWED
  version   = models.CharField(max_length=22, default='0.1')

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


  @property
  def highlights(self):
    """
    highlights 
    """
    return filter(None, self.comments.exclude(status='deleted').values_list('highlights', flat=True))


  @property
  def ogcover(self):
    """
    cover url to be used in og meta headers
    """
    cover = self.covers.first()
    return cover


  @property
  def isCollection(self):
    if not hasattr(self, '_isCollection'):
      self._isCollection = self.tags.filter(slug='collection').count() > 0
      return self._isCollection
    else:
      return self._isCollection

  # set the plural name and fix the default sorting order
  class Meta:
    ordering = ('-date_last_modified',)
    verbose_name_plural = 'stories'

  
  # get story path based on random generated shorten url
  def get_path(self):
    return os.path.join(self.owner.profile.get_path(), self.short_url+ '.md')


  def get_git_path(self):
    return 'users/%s/%s.md' % (self.owner.profile.short_url, self.short_url)

  
  def get_absolute_url(self):
    return u"/story/%s" % self.slug


  def __unicode__(self):
    return '%s - by %s' % (self.title, self.owner.username)

  # store into the whoosh index
  def store(self, ix=None, receiver=None):
    logger.debug('story {pk:%s} whoosh init %s' % (self.pk, receiver))
      
    if settings.TESTING:
      logger.debug('story {pk:%s} whoosh skipped, jus testing! %s' % (self.pk, receiver))
      return

    if ix is None:
      ix = helpers.get_whoosh_index()

    authors   =  u", ".join([u'%s' % t.fullname for t in self.authors.all()])
    tags      = u",".join([u'%s' % t.slug for t in self.tags.all()])
    writer    = ix.writer()
    try:
      metadata  = json.loads(self.metadata)
    except Exception as e:
      logger.exception(e)
      return

    # multilingual abstract, reduced
    abstracts = u"\n".join(filter(None,list(set([metadata['abstract'][language_code] if language_code in metadata['abstract'] else None for dlc, l, language_code in settings.LANGUAGES]))))
    titles    = u"\n".join(filter(None,list(set([metadata['title'][language_code] if language_code in metadata['title'] else None for dlc, l, language_code in settings.LANGUAGES]))))

    writer.update_document(
      title     = titles,
      abstract  = abstracts,
      path      = u"%s"%self.short_url,
      content   = u"\n".join(BeautifulSoup(markdown(u"\n\n".join(filter(None,[
        self.contents,
      ])), extensions=['footnotes'])).findAll(text=True)),
      tags      = tags,
      authors   = authors,
      status    = u"%s" % self.status,
      classname = u"story")
    # print "saving",  u",".join([u'%s' % t.slug for t in self.tags.all()])
    writer.commit()
    logger.debug('story {pk:%s} whoosh completed %s' % (self.pk, receiver))

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
    if not contents:
      # we force to use # headers by setting the threshold of 3 so that h1 "===" is transformed to h3 "###"
      contents = pypandoc.convert_file(self.source.path, 'markdown',  extra_args=['--base-header-level=3'])
      # ... but we have to transform them back, minus a level (e.g. transformed h1 becomes h2).
      # We should check if we can use the pandoc options for that directly
      self.contents = re.sub(r'#(#+)', r'\1', contents) 
    else:
      logger.debug('story {pk:%s} already contains contents. Skipped.' % self.pk)


  def gitTag(self, tag):
    """
    Convenient function to handle GIT tagging
    """
    repo = Repo.init(settings.GIT_ROOT)
    repo.tag(tag)


  def gitLog(self, limit=4, offset=0):
    from django.utils import timezone
    from datetime import datetime
    repo = Repo.init(settings.GIT_ROOT)
    path = self.get_git_path()
    git  = repo.git()

    # coms = helpers.get_previous_and_next(repo.iter_commits(paths=path, max_count=limit, skip=offset))
    coms = helpers.get_previous_and_next(list(repo.iter_commits(paths=path, max_count=limit, skip=offset)))
    logs = []

    for cprev, commit, cnext in coms:
      logs.append({
        'hexsha': commit.hexsha,
        'author': commit.author.email,
        'date': datetime.fromtimestamp(commit.authored_date),
        'diff': repo.git.diff(commit, cnext, path) if cnext else None
      })
      
    # # # print repo.git.diff(commits_touching_path[0], commits_touching_path[1], path)
    # #   print repo.git.diff(pairs[0], pairs[1], path)
    # for cprev, com, cnext in coms:
    #   if cnext:
    #     print repo.git.diff(com, cnext, path)
    return logs

        

  def gitBlob(self, commit_id):
    repo = Repo.init(settings.GIT_ROOT)
    # relative path to repo
    path = self.get_git_path()
    
    logger.debug('story {pk:%s} git show %s:%s' % (self.pk, commit_id, path))
  
    try:
      file_contents = repo.git.show('%s:%s'%(commit_id,path))
    except Exception as e:
      logger.exception(e)
      return None

    return file_contents



  def gitCommit(self):
    """
    convenient function to commit the story
    """
    logger.debug('story {pk:%s} gitCommit: %s' % (self.pk, self.get_path()))
  
    path = self.get_path()
    dirpath = os.path.dirname(path)

    # check that the dir path is accessible
    if not os.path.exists(dirpath):
      logger.debug('story {pk:%s} gitCommit: path "%s" not found, owner changed?' % (self.pk, path))
      try:
        owner_path = os.path.dirname(self.owner.profile.get_path())
        os.makedirs(owner_path)
        logger.debug('story {pk:%s} gitCommit: owner_path created at %s.' % (self.pk, owner_path))
      
      except OSError as e:
        if e.errno != errno.EEXIST:
          logger.exception(e)
      except Exception as e:
        logger.exception(e)

    try:   
      f = codecs.open(path, encoding='utf-8', mode='w+')
      f.write(self.contents)
      f.seek(0)
      f.close()
      logger.debug('story {pk:%s} gitCommit: md file "%s" written.' % (self.pk, path))
    except Exception as e:
      logger.exception(e)

    if settings.TESTING:
      logger.debug('story {pk:%s} gitCommit skipped, just testing!' % self.pk)
      return
    
    author = Actor(self.owner.username, self.owner.email)
    committer = Actor(settings.GIT_COMMITTER['name'], settings.GIT_COMMITTER['email'])

    # commit if there are any differences
    repo = Repo.init(settings.GIT_ROOT)

    # add and commit JUST THIS FILE
    #tree = Tree(repo=repo, path=self.owner.profile.get_path())
    try:
      repo.index.add([path])
      c = repo.index.commit(message=u"saving %s" % self.title, author=author, committer=committer)
    except IOError as e:
      logger.debug('story {pk:%s} gitCommit has errors.' % self.pk)
      logger.exception(e)

    logger.debug('story {pk:%s} gitCommit done.' % self.pk)


  # convert the last saved content (markdown file) to a specific format (default: docx)
  # the media will be in the user MEDIA folder...
  def download(self, outputFormat='docx', language=None, extension=None):
    outputfile = user_path(self, '%s-%s.%s' % (
      self.short_url,
      self.date_last_modified.strftime("%s"), 
      extension if extension is not None else outputFormat
    ), True)
    
    if os.path.exists(outputfile):
      print "do not regenerate", outputfile, self.date_last_modified.strftime("%s")
      return outputfile

    tempoutputfile = user_path(self, '__%s.md' % self.short_url)
    logger.debug('story {pk:%s} creating temp file.' % self.pk)
    authors   =  u", ".join([u'%s' % t.fullname for t in self.authors.all()])
    tags      = u",".join([u'%s' % t.slug for t in self.tags.filter(category=Tag.KEYWORD)])
    
    # rewrite links for interactive PDF
    with codecs.open(tempoutputfile, "w", "utf-8") as temp:
      temp.write(u'\n\n'.join([
        # u"#%s" % self.title,
        # u"> %s" % self.abstract if self.abstract else "",
        # generate citation, signatures
        self.contents
      ]))

    # reverted = re.sub(r'#(#+)', r'\1', contents) 
    pypandoc.convert_file(tempoutputfile, outputFormat, outputfile=outputfile, 
      extra_args=[
        '--base-header-level=1', 
        '--latex-engine=xelatex',
        '--template=%s' % settings.MILLER_TEX,
        '-V', 'geometry:top=2.5cm, bottom=2.5cm, left=2.5cm, right=2.5cm',
        '-V', 'footer=%s' % settings.MILLER_TITLE,
        '-V', 'title=%s' % self.title.replace('&', '\&'),
        '-V', 'author=%s' % ', '.join([u'%s (%s)' % (a.fullname, a.affiliation) for a in self.authors.all()]),
        '-V', 'keywords=%s' % tags,
        '-V','abstract=%s' % self.abstract.replace('&', '\&') if self.abstract else ''
      ])
    # once done,
    os.remove(tempoutputfile)

    return outputfile

  def send_email_to_staff(self, template_name, extra=None):
    """
    Send email to staff, to the settings.DEFAULT_FROM_EMAIL address.
    """
    recipient = settings.DEFAULT_FROM_EMAIL
    if recipient:
      logger.debug('story {pk:%s} sending email to DEFAULT_FROM_EMAIL {email:%s}...' % (self.pk, settings.DEFAULT_FROM_EMAIL))
      context = {
        'title':    self.title,
        'abstract': self.abstract,
        'slug':     self.slug,
        'first_author': self.owner.authorship.first(),
        'username': 'staff member',
        'site_name': settings.MILLER_TITLE,
        'site_url':  settings.MILLER_SETTINGS['host']
      }
      if extra:
        context.update(extra)
      send_templated_mail(template_name=template_name, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[recipient], context=context)
    else:
      logger.debug('story {pk:%s} cannot send email to recipient, settings.DEFAULT_FROM_EMAIL not found!' % (self.pk))
      

  def send_email_to_author(self, author, template_name):
    """
    Send email to staff, to the settings.DEFAULT_FROM_EMAIL address.
    """
    recipient = [author.user.email]
    if recipient:
      logger.debug('story {pk:%s} sending email to author {username:%s}...' % (self.pk, author.user.username))
      try:
        send_templated_mail(template_name=template_name, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=recipient, fail_silently=False, context={
          'title':    self.title,
          'abstract': self.abstract,
          'slug':     self.slug,
          # 'authors':  self.authors.all(),
          'author':   author,
          'site_name': settings.MILLER_TITLE,
          'site_url':  settings.MILLER_SETTINGS['host']
        })
      except Exception as e:
        logger.exception(e)
    else:
      logger.debug('story {pk:%s} cannot send email to recipient, not found fo author {pk:%s}' % (self.pk,author.pk))
      


  # hook init so that during save we won't keep data
  def __init__(self, *args, **kwargs):
    super(Story, self).__init__(*args, **kwargs)
    self._original = (
      ('status', self.status),
      ('metadata', self.metadata),
      ('contents', self.contents),
      ('date', self.date),
    )


  # check if the saveable instance differs from the original stored one. Cfr the overriding of __init__ function
  def has_diffs(self, exclude=None):
    for field, value in self._original:
      if exclude is not None and field == exclude:
        continue
      if getattr(self, field) != value:
        return True
    return False


  # save hook
  def save(self, *args, **kwargs):
    if not hasattr(self, '_saved'):
      self._saved = 1
    else:
      self._saved = self._saved + 1
    logger.debug('story@save  {pk:%s} init save, time=%s' % (self.pk, self._saved))
    
    # check slug
    if not self.slug:
      self.slug = helpers.get_unique_slug(self, self.title, max_length=68)
      logger.debug('story@save {pk:%s, slug:%s} slug generated.' % (self.pk, self.slug))
    else:
      logger.debug('story@save {pk:%s} slug ok.' % self.pk)

    if self.date is None:
      logger.debug('story@save {slug:%s,pk:%s} not having a default date. Fixing...' % (self.slug, self.pk))
      self.date = self.date_last_modified
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
          if language_code not in metadata['title'] or not metadata['title'][language_code]:
            metadata['title'][language_code] = self.title

          if language_code not in metadata['abstract'] or not metadata['abstract'][language_code]:
            metadata['abstract'][language_code] = self.abstract

        logger.debug('metadata filled.')
        self.metadata = json.dumps(metadata, ensure_ascii=False, indent=1)
      except Exception as e:
        logger.exception(e)


    logger.debug('story@save {slug:%s,pk:%s} completed, ready to dispatch @postsave, time=%s' % (self.slug, self.pk, self._saved))
    super(Story, self).save(*args, **kwargs)


# handle redis cache correctly
@receiver(pre_save, sender=Story)
def clear_cache_on_save(sender, instance, **kwargs):
  ckey = 'story.%s' % instance.short_url
  cache.delete(ckey)
  logger.debug('story@pre_save {pk:%s, short_url:%s} cache deleted.' % (instance.pk,instance.short_url))


# generic story_ready handlers ;) store in whoosh
@receiver(post_save, sender=Story)
def dispatcher(sender, instance, created, **kwargs):
  """
  Generic post_save handler. Dispatch a story_ready signal.
  If receiver need to update the instance, they just need to put the property `_dirty`
  """
  if not hasattr(instance, '_dispatcher'):
    instance._dispatcher = True
  else:
    logger.debug('story@post_save {pk:%s} dispatching already dispatched. Skipping.' % instance.pk)
    return
  # dispatch (call). 
  logger.debug('story@post_save {pk:%s} dispatching @story_ready...' % instance.pk)
  
  story_ready.send_robust(sender=sender, instance=instance, created=created)
  
  if getattr(instance, '_dirty', None) is not None:
    logger.debug('story@post_save {pk:%s} instance is dirty. Need to call instance.save()..' % instance.pk)
    instance.save()
  else:
    logger.debug('story@post_save  {pk:%s} no need to save the instance again.' % instance.pk)
  
  if created:  
    action.send(instance.owner, verb='created', target=instance)
    follow(instance.owner, instance, actor_only=False)
  elif instance.status != Story.DRAFT and instance.has_diffs(exclude='status'):
    # something changed in a NON DRAFT document.
    pass
    # action.send(instance.owner, verb='updated', target=instance)


# store in whoosh
@receiver(story_ready, sender=Story)
def store_working_md(sender, instance, created, **kwargs):
  instance.store()
  logger.debug('story@story_ready {pk:%s} store_working_md: done' % instance.pk)


@receiver(story_ready, sender=Story)
def create_first_author(sender, instance, created, **kwargs):
  if created:
    author = instance.owner.authorship.first()
    instance.authors.add(author)
    instance._dirty = True
    logger.debug('story@story_ready {pk:%s} add author {fullname:%s}" done.' % (instance.pk, author.fullname))




# clean store in whoosh when deleted
@receiver(pre_delete, sender=Story)
def unstore_working_md(sender, instance, **kwargs):
  instance.unstore()
  logger.debug('story@pre_delete {pk:%s} unstore_working_md: done' % instance.pk)


# check if there is a source file of type docx attached and transform it to content.
@receiver(story_ready, sender=Story)
def transform_source(sender, instance, created, **kwargs):
  # print 'story is created?', instance.pk, created
  if not created:
    return
  if bool(instance.source):
    logger.debug('story@story_ready {pk:%s} transform_source: converting...' % instance.pk)
    instance.convert()
    instance._dirty = True
  else:
    logger.debug('story@story_ready {pk:%s} transform_source: skipping.' % instance.pk)
  
  
  logger.debug('story@story_ready {pk:%s} transform_source: done' % instance.pk)




# create story file if it is not exists; if the story eists already, cfr the followinf story_ready
@receiver(story_ready, sender=Story)
def create_working_md(sender, instance, created, **kwargs):
  logger.debug('story@story_ready {pk:%s}: create_working_md...' % instance.pk)
  try:
    instance.gitCommit()
  except Exception as e:
    logger.exception(e)
  logger.debug('story@story_ready {pk:%s}: create_working_md done.' % instance.pk)


@receiver(story_ready, sender=Story)
def if_status_changed(sender, instance, created, **kwargs):
  """
  this function enable actions for status change activity:e.g. from draft to editing
  for editing to Review.
  """
  logger.debug('story@story_ready {pk:%s, status:%s} check if_status_changed' % (instance.pk, instance.status))

  if created:
    instance.send_email_to_staff(template_name='story_created')

  # if status really changed.
  if hasattr(instance, '_original') and instance.status != instance._original[0][1]:
    logger.debug('(story@story_ready {pk:%s, status:%s} @story_ready if_status_changed from %s' % (instance.pk, instance.status, instance._original[0][1]))
    if instance.status == Story.PUBLIC:
      # send email to the authors profile emails and a confirmation email to the current address: the story has been published!!!
      action.send(instance.owner, verb='got_published', target=instance)
    elif instance.status == Story.PENDING:
      # send email to staff
      instance.send_email_to_staff(template_name='story_pending_for_staff')

      # send email to authors
      authors = instance.authors.exclude(user__email__isnull=True)
      
      for author in authors:
        instance.send_email_to_author(author=author, template_name='story_pending_for_author')
        
      action.send(instance.owner, verb='ask_for_publication', target=instance)
    elif instance.status == Story.EDITING:
      # send email.
      action.send(instance.owner, verb='ask_for_editing', target=instance)
    elif instance.status == Story.REVIEW:
      # send email.
      instance.send_email_to_staff(template_name='story_review_for_staff')
      action.send(instance.owner, verb='ask_for_review', target=instance)
    elif instance.status == Story.REVIEW_DONE:
      closingremarks = instance.reviews.filter(category='closing').select_related('assignee').first()
      
      try:
        instance.send_email_to_staff(template_name='story_reviewdone_for_staff', extra={
          #chief decision:
          'closingremarks': closingremarks,
          'reviews': instance.reviews.filter(category='double')
        })
      except Exception as e:
        print e

# clean makdown version and commit
@receiver(pre_delete, sender=Story)
def delete_working_md(sender, instance, **kwargs):
  logger.debug('story@pre_delete {pk:%s} delete file: %s' % (instance.pk, instance.get_path()))
  
  path = instance.get_path()
  

  from git import Repo, Commit, Actor, Tree

  author = Actor(instance.owner.username, instance.owner.email)
  committer = Actor(settings.GIT_COMMITTER['name'], settings.GIT_COMMITTER['email'])

  # /* delete file */
  try:
    os.remove(path);
  except OSError as e:
    # it has been canceled already
    pass
  except Exception as e:
    logger.exception(e)
  # keep exports in .gitignore

  logger.debug('story@pre_delete {pk:%s} markdown removed.' % instance.pk)

  if settings.TESTING:
    logger.debug('story@pre_delete {pk:%s} delete_working_md skipped commit, just testing!' % instance.pk)
    return

  # commit if there are any differences
  repo = Repo.init(settings.GIT_ROOT)

  # add and commit JUST THIS FILE
  #tree = Tree(repo=repo, path=instance.owner.profile.get_path())
  repo.git.add(update=True)
  repo.index.commit(message=u"deleting %s" % instance.title, author=author, committer=committer)


  logger.debug('story@pre_delete {pk:%s} removed from git.' % instance.pk)


@receiver(pre_delete, sender=Story)
def delete_cache_on_save(sender, instance, **kwargs):
  ckey = 'story.%s' % instance.short_url
  cache.delete(ckey)
  logger.debug('story@pre_delete {pk:%s} delete_cache_on_save: done' % instance.pk)


@receiver(m2m_changed, sender=Story.tags.through)
def store_tags(sender, instance, **kwargs):
  if kwargs['action'] == 'post_add' or kwargs['action'] == 'post_remove':
    instance.store(receiver='m2m_changed tags')
    ckey = 'story.%s' % instance.short_url
    cache.delete(ckey)
    cache.delete('story.featured')


@receiver(m2m_changed, sender=Story.covers.through)
def store_tags(sender, instance, **kwargs):
  if kwargs['action'] == 'post_add' or kwargs['action'] == 'post_remove':
    ckey = 'story.%s' % instance.short_url
    cache.delete(ckey)


@receiver(m2m_changed, sender=Story.authors.through)
def store_authors(sender, instance, **kwargs):
  if kwargs['action'] == 'post_add' or kwargs['action'] == 'post_remove':
    instance.store(receiver='m2m_changed authors')
    ckey = 'story.%s' % instance.short_url
    cache.delete(ckey)


