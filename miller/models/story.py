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


  date               = models.DateTimeField(auto_now_add=True, db_index=True, blank=True, null=True) # date displayed (metadata)
  date_created       = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  status    = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT, db_index=True)
  priority  = models.PositiveIntegerField(default=0, db_index=True)

  owner     = models.ForeignKey(User); # at least the first author, the one who owns the file.
  
  authors   = models.ManyToManyField(Author, related_name='stories', blank=True) # collaborators
  documents = models.ManyToManyField(Document, related_name='stories', through='Caption', blank=True)

  stories   = models.ManyToManyField("self", through='Mention', symmetrical=False, related_name='mentioned_to')

  # store the git hash for current gitted self.contents. Used for comments.
  version   = models.CharField(max_length=22, default='', help_text='store the git hash for current gitted self.contents.', blank=True)

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
  def isSourceAvailable(self):
    return hasattr(self.source, 'url')

  @property
  def highlights(self):
    """
    highlights 
    """
    return filter(None, self.comments.exclude(status='deleted').filter(version=self.version).values_list('highlights', flat=True))


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


  @property
  def diffs(self):
    """
    check if the saveable instance differs from the original stored one.
    This model __init__ function produces the 'original' tuple
    """
    try:
      return self._diffs
    except AttributeError:
      pass

    self._diffs = []

    for field, value in self._original:
      if getattr(self, field, None) != value:
        self._diffs.append(field)
    return self._diffs

  # set the plural name and fix the default sorting order
  class Meta:
    ordering = ('-date_last_modified',)
    verbose_name_plural = 'stories'

  
  def get_cache_key(self, extra=None):
    """
    get current cachekey name  based on random generated shorten url
    (to be used in redis cache)
    """
    return 'story.%s.%s' % (self.short_url, extra) if extra else 'story.%s' % self.short_url


  def get_path(self):
    """
    get absolute md filepath based on random generated shorten url
    """
    return os.path.join(self.owner.profile.get_path(), self.short_url + '.md')


  def get_git_path(self):
    """
    get  md filepath relative to git root specified in settings.GIT_ROOT,
    based on random generated shorten url
    """
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


  def write_contents(self):
    """
    Write current Story contents to the filepath specified by self.get_path() 
    """
    path = self.get_path()

    if not self.version:
      # if self.version exists, the file has been saved before.
      if not os.path.exists(path):
        dirpath = os.path.dirname(path)
        try:
          # create directory path.
          os.makedirs(dirpath)
        except OSError as e:
          if e.errno != errno.EEXIST:
            raise e

    try:
      f = codecs.open(path, encoding='utf-8', mode='w+')
      f.write(self.contents)
      f.seek(0)
      f.close()
    except Exception as e:
      logger.exception(e)
    else:
      logger.debug('story {pk:%s} contents written.' % (self.pk))


  def commit_contents(self, force=False):
    """
    Convenient function to commit the Story contents filepath.
    Internally it makes use of Story `diffs` property
    and check if contents has changed before committing.
    """
    if self.pk and not 'contents' in self.diffs:
      logger.debug('story {pk:%s} commit_contents skipped, nothing new to commit.' % (self.pk))
      return
    
    

    if not force and settings.TESTING:
      logger.debug('story {pk:%s} commit_contents git commit skipped, just testing!' % self.pk)
      return
    
    author = Actor(self.owner.username, self.owner.email)
    committer = Actor(settings.GIT_COMMITTER['name'], settings.GIT_COMMITTER['email'])

    # commit if there are any differences
    repo = Repo.init(settings.GIT_ROOT)

    # add and commit JUST THIS FILE
    #tree = Tree(repo=repo, path=self.owner.profile.get_path())
    try:
      repo.index.add([self.get_path()])
      c = repo.index.commit(message=u"saving %s" % self.title, author=author, committer=committer)
      short_sha = repo.git.rev_parse(c, short=4)
    except IOError as e:
      logger.debug('story {pk:%s} gitCommit has errors.' % self.pk)
      logger.exception(e)
    print c
    self.version = short_sha
    logger.debug('story {pk:%s} gitCommit {hash:%s,short:%s} done.' % (self.pk, c, short_sha))


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


  def send_smart_email(self, recipient, template_name, from_email=settings.DEFAULT_FROM_EMAIL, extra={}):
    if not settings.EMAIL_HOST and not settings.TESTING:
      logger.warning('story {pk:%s} email %s cannot be send, settings.EMAIL_HOST is not set.' % (self.pk, template_name))
      return
    recipient_list = [recipient if isinstance(recipient, basestring) else recipient.email]
    context = {
      'recipient': recipient,
      'story': self,
      'site_name': settings.MILLER_TITLE,
      'site_url':  settings.MILLER_SETTINGS['host'],
    }
    context.update(extra)
    try:
      send_templated_mail(template_name=template_name, from_email=from_email, recipient_list=recipient_list, context=context)
    except Exception as e:
      logger.exception(e)
    else:
      logger.debug('story {pk:%s} email %s sent' % (self.pk, template_name))
  

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
      

  def create_first_author(self):
    author = self.owner.authorship.first()
    self.authors.add(author)
    logger.debug('story {pk:%s} create first author {fullname:%s}" done.' % (self.pk, author.fullname))


  def dispatch_status_changed(self, created):
    """
    this function dispatches messages whenever a story status changes.
    e.g. from draft to pending
    for editing to Review.
    """
    if created:
      self.send_smart_email(recipient=settings.DEFAULT_FROM_EMAIL, template_name='story_created_for_staff')

    if 'status' in self.diffs:
      logger.debug('story {pk:%s} status changed from %s to %s' % (self.pk, self._original[0][1], self.status))

      if self.status == Story.PUBLIC:
        # send email to the authors profile emails and a confirmation email to the current address: the story has been published!!!
        action.send(self.owner, verb='got_published', target=self)
      elif self.status == Story.PENDING:
        # send email to staff
        self.send_email_to_staff(template_name='story_pending_for_staff')
        # send email to authors
        authors = self.authors.exclude(user__email__isnull=True)
      
        for author in authors:
          self.send_email_to_author(author=author, template_name='story_pending_for_author')
        
        # chief reviewer if not belonging to authors as well @todo
        action.send(self.owner, verb='ask_for_publication', target=self)
      elif self.status == Story.EDITING:
        # DEPRECATED, not used.
        action.send(self.owner, verb='ask_for_editing', target=self)
      elif self.status == Story.REVIEW:
        # story is under review.
        self.send_email_to_staff(template_name='story_review_for_staff')
        action.send(self.owner, verb='ask_for_review', target=self)
      elif self.status == Story.REVIEW_DONE:
        # chief reviewer has closed the review process.
        closingremarks = self.reviews.filter(category='closing').select_related('assignee').first()
        
        self.send_email_to_staff(template_name='story_reviewdone_for_staff', extra={
          #chief decision:
          'closingremarks': closingremarks,
          'reviews': self.reviews.filter(category='double')
        })
        # send mail to chief reviewer @todo


  def __init__(self, *args, **kwargs):
    """
    Store original values internally.
    used in Story method `dispatch_status_changed`
    """
    super(Story, self).__init__(*args, **kwargs)
    self._original = (
      ('status', self.status),
      ('metadata', self.metadata),
      ('contents', self.contents),
    )

  
  def save(self, *args, **kwargs):
    """
    perform save
    """
    self._saved = getattr(self, '_saved', 0)
    self._saved = self._saved + 1
    logger.debug('story@save  {pk:%s} init save, time=%s' % (self.pk, self._saved))
    
    # check slug
    if not self.slug:
      self.slug = helpers.get_unique_slug(self, self.title, max_length=68)
      logger.debug('story@save {pk:%s, slug:%s} slug generated.' % (self.pk, self.slug))

    if self.date is None:
      logger.debug('story@save {slug:%s,pk:%s} not having a default date. Fixing...' % (self.slug, self.pk))
      self.date = self.date_last_modified

    # create story file if it is not exists; if the story eists already, cfr the followinf story_ready
    if self._saved == 1:
      try:
        self.write_contents()
        self.commit_contents()
      except Exception as e:
        logger.exception(e)
      else:
        logger.debug('story@save {pk:%s}: write_contents_to_path done.' % self.pk)


    logger.debug('story@save {slug:%s,pk:%s} completed, ready to dispatch @postsave, time=%s' % (self.slug, self.pk, self._saved))
    super(Story, self).save(*args, **kwargs)
    



@receiver(pre_save, sender=Story)
def clear_cache_on_save(sender, instance, **kwargs):
  """
  Clean current story from cache.
  """
  if getattr(instance, '_dirty', None) is not None:
    return
  # ckey = # 'story.%s' % instance.short_url
  cache.delete_pattern('%s*' % instance.get_cache_key())
  logger.debug('story@pre_save {pk:%s, short_url:%s} cache deleted.' % (instance.pk,instance.short_url))




@receiver(pre_save, sender=Story)
def fill_metadata(sender, instance, **kwargs):
  if getattr(instance, '_dirty', None) is not None:
    return
  try:
    metadata = instance.dmetadata
    if 'title' not in metadata:
      metadata['title'] = {}
    if 'abstract' not in metadata:
      metadata['abstract'] = {}
    for default_language_code, label, language_code in settings.LANGUAGES:
      if default_language_code not in metadata['title']:
        metadata['title'][language_code] = instance.title
      if default_language_code not in metadata['abstract']:
        metadata['abstract'][language_code] = instance.abstract
      if language_code not in metadata['title']:
        metadata['title'][language_code] = ''
      if language_code not in metadata['abstract']:
        metadata['abstract'][language_code] = ''
    instance.metadata = json.dumps(metadata, ensure_ascii=False, indent=1)
  except Exception as e:
    logger.exception(e)
  else:
    logger.debug('story@pre_save {pk:%s}: metadata ready.' % instance.pk)




# generic story_ready handlers ;) store in whoosh
@receiver(post_save, sender=Story)
def dispatcher(sender, instance, created, **kwargs):
  """
  Generic post_save handler. Dispatch a story_ready signal.
  If receiver need to update the instance, they just need to put the property `_dirty`
  """
  if created and not kwargs['raw']:  
    action.send(instance.owner, verb='created', target=instance)
    follow(instance.owner, instance, actor_only=False)
  
  if not kwargs['raw']:
    # send emails if status has changed.
    instance.dispatch_status_changed(created)

  # always store in whoosh.
  instance.store()


# clean store in whoosh when deleted
@receiver(pre_delete, sender=Story)
def unstore_working_md(sender, instance, **kwargs):
  instance.unstore()
  logger.debug('story@pre_delete {pk:%s} unstore_working_md: done' % instance.pk)


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
  cache.delete_pattern('%s*' % instance.get_cache_key())
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


