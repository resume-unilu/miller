#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pypandoc, re, os, codecs, json, logging, errno
import django.dispatch

from actstream import action
from actstream.actions import follow

from BeautifulSoup import BeautifulSoup

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.search import SearchVectorField

from django.core.signals import request_finished
from django.core.cache import cache
from django.db import models
from django.db.models.signals import pre_delete, post_save, m2m_changed, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.template.loader import get_template
from weasyprint import HTML

# from jsonfield import JSONField
from git import Repo, Commit, Actor, Tree

from markdown import markdown

from miller import helpers
from miller.models import Tag, Document, Author

from pydash import py_

# from simplemde.fields import SimpleMDEField
from templated_email import send_templated_mail

logger = logging.getLogger('miller.commands')

story_ready = django.dispatch.Signal(providing_args=["instance", "created"])


def user_path(instance, filename, safeOrigin=False):
  root, ext = os.path.splitext(filename)
  src = os.path.join(settings.MEDIA_ROOT,
                     instance.owner.profile.short_url if not settings.TESTING else 'test_%s' % instance.owner.username,
                     instance.short_url + ext if not safeOrigin else filename)
  return src


class Story(models.Model):
  language_dict = helpers.get_languages_dict()

  DRAFT = 'draft'  # visible just for you and staff users
  SHARED = 'shared'  # share with specific user
  PUBLIC = 'public'  # everyone can access that.
  # status related to review process.
  PENDING = 'pending'
  EDITING = 'editing'  # only staff and editors access this
  REVIEW = 'review'  # staff, editors and reviewer acces this
  REVIEW_DONE = 'reviewdone'
  PRE_PRINT = 'preprint'  # in this status and whenever is public, we ask the author to comment his commit on each save to better trace history

  DELETED = 'deleted'  # will be sent to the bin
  # REFUSED  = 'refused' # will be sent to the bin

  STATUS_CHOICES = (
    (DRAFT, 'draft'),
    (SHARED, 'shared'),
    (PUBLIC, 'public'),  # accepted paper.
    (DELETED, 'deleted'),

    (PENDING, 'pending review'),  # ask for publication, pending review
    (EDITING, 'editing'),  # ask for editing review
    (REVIEW, 'review'),  # under review
    (REVIEW_DONE, 'review done'),
    (PRE_PRINT, 'pre print')
  )

  short_url = models.CharField(max_length=22, db_index=True, default=helpers.create_short_url, unique=True)

  title = models.CharField(max_length=500)
  slug = models.CharField(max_length=140, unique=True, blank=True,
                          db_index=True)  # force the unicity of the slug (story lookup from the short_url)
  abstract = models.CharField(max_length=2000, blank=True, null=True)
  contents = models.TextField(verbose_name=u'mardown content', default='',
                              blank=True)  # It will store the last markdown contents.
  metadata = models.TextField(default=json.dumps({
    'title': language_dict,
    'abstract': language_dict
  }, indent=1), blank=True)  # it will contain, JSON fashion

  data = JSONField(verbose_name=u'metadata contents', help_text='JSON format', default=dict(), blank=True)

  date = models.DateTimeField(db_index=True, blank=True, null=True)  # date displayed (metadata)
  date_created = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT, db_index=True)
  priority = models.PositiveIntegerField(default=0, db_index=True)

  owner = models.ForeignKey(User);  # at least the first author, the one who owns the file.

  authors = models.ManyToManyField(Author, related_name='stories', blank=True)  # collaborators
  documents = models.ManyToManyField(Document, related_name='stories', through='Caption', blank=True)

  stories = models.ManyToManyField("self", through='Mention', symmetrical=False, related_name='mentioned_to')

  # store the git hash for current gitted self.contents. Used for comments.
  version = models.CharField(max_length=22, default='',
                             help_text='store the git hash for current gitted self.contents.', blank=True)

  # the leading document(s), e.g. an interview
  covers = models.ManyToManyField(Document, related_name='covers', blank=True)

  tags = models.ManyToManyField(Tag, blank=True)  # tags

  # cover thumbnail, e.g. http://www.eleganzadelgusto.com/wordpress/wp-content/uploads/2014/05/Marcello-Mastroianni-for-Arturo-Zavattini.jpg
  cover = models.URLField(max_length=500, blank=True, null=True)

  # cover copyright or caption, markdown flavoured. If any
  cover_copyright = models.CharField(max_length=140, blank=True, null=True)

  # fileField
  source = models.FileField(upload_to=user_path, blank=True, null=True)

  # fileField (usually a zotero-friendly importable file)
  bibliography = models.FileField(upload_to=user_path, blank=True, null=True)

  # add huge search field
  search_vector = SearchVectorField(null=True, blank=True)

  @property
  def dmetadata(self):
    if not hasattr(self, '_dmetadata'):
      try:
        self._dmetadata = json.loads(self.metadata)
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
    return self.get_highlights_by_commit(commit_id=self.version)
    # filter(None, self.comments.exclude(status='deleted').filter(version=self.version).values_list('highlights', flat=True))

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

  def get_DOI_title(self):
    """
    Return the title for DOI based on curren tsettings
    """
    # tags = self.tags.all()
    _title = self.title
    tags = []

    if settings.MILLER_DOI_TAG_SLUGS_FOR_TITLE:
      tags = [t.name for t in self.tags.filter(slug__in=settings.MILLER_DOI_TAG_SLUGS_FOR_TITLE)]

    if settings.MILLER_DOI_TAG_CATEGORIES_FOR_TITLE:
      tags = tags + [t.name for t in self.tags.filter(category__in=settings.MILLER_DOI_TAG_CATEGORIES_FOR_TITLE)]

    if tags:
      _title = u'{0}. {1}'.format(_title.strip('. \t\n\r'), u', '.join([t for t in tags]))

    return _title

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

  def save_captions_from_contents(self, key='pk', parser='json'):
    """
    Analyse contents looking for document slug or pk, based on your current settings.
    Return a tuple
    """
    expecting = []  # list of keys we expect to find in the db
    missing = []  # list of keys not found in the db
    saved = []  # Caption relationships saved

    docs = []  # documents to be saved

    if parser == 'json':
      try:
        json_contents = json.loads(self.contents)
      except Exception as e:
        # handle this at API level
        raise e

      # look for the keys based on your settings
      expecting = helpers.get_values_from_dict(json_contents, key=key)

      # save relationships, handle errors
      docs = Document.objects.filter(**{'%s__in' % key: expecting})

      if docs.count() != len(expecting):
        # calculate diff!    
        missing = list(set(expecting) - set(docs.values_list(key, flat=True)))

    # clear list of captions
    captions = self.caption_set.all().delete()

    # model (so we don't reference to Caption here ;)
    ThroughModel = Story.documents.through

    # save captions
    saved = ThroughModel.objects.bulk_create([ThroughModel(document=d, story=self) for d in docs])

    return saved, missing, expecting

  # store into the whoosh index
  def store(self, ix=None, receiver=None):
    logger.debug('story {pk:%s} whoosh init %s' % (self.pk, receiver))

    if settings.TESTING:
      logger.debug('story {pk:%s} whoosh skipped, jus testing! %s' % (self.pk, receiver))
      return

    if ix is None:
      ix = helpers.get_whoosh_index()

    authors = u", ".join([u'%s' % t.fullname for t in self.authors.all()])
    tags = u",".join([u'%s' % t.slug for t in self.tags.all()])
    writer = ix.writer()
    try:
      metadata = json.loads(self.metadata)
    except Exception as e:
      logger.exception(e)
      return

    # multilingual abstract, reduced
    abstracts = u"\n".join(
      filter(None, list(set(py_.get(metadata, 'abstract.%s' % lang[2], None) for lang in settings.LANGUAGES))))
    titles = u"\n".join(
      filter(None, list(set(py_.get(metadata, 'title.%s' % lang[2], None) for lang in settings.LANGUAGES))))

    writer.update_document(
      title=titles,
      abstract=abstracts,
      path=u"%s" % self.short_url,
      content=u"\n".join(BeautifulSoup(markdown(u"\n\n".join(filter(None, [
        self.contents,
      ])), extensions=['footnotes'])).findAll(text=True)),
      tags=tags,
      authors=authors,
      status=u"%s" % self.status,
      classname=u"story")
    # print "saving",  u",".join([u'%s' % t.slug for t in self.tags.all()])
    writer.commit()
    logger.debug('story {pk:%s} whoosh completed %s' % (self.pk, receiver))

  @staticmethod
  def get_search_Q(query, raw=False):
    """
    Return search queryset for this model, ranked by weight. Check update_search_vector function for more info
    """
    from miller.postgres import RawSearchQuery

    # ' & '.join(map(lambda x: x if x.endswith(':*') else '%s:*' % x, query.split(' ')))
    return models.Q(search_vector=RawSearchQuery(query, config='simple'))

  def update_search_vector(self):
    """
    Fill the search_vector using self.data:
    e.g. get data['title'] if is a basestring or data['title']['en_US'] according to the values contained into settings.LANGUAGES
    Note that a language configuration can be done as well, in this case consider the last value in settings.LANGUAGES (e.g. 'english')
    Then fill search_vector with authors and tags.
    """
    from django.db import connection
    fields = (('title', 'A'), ('abstract', 'B'))
    contents = []

    for _field, _weight in fields:
      default_value = self.data.get(_field, None)
      value = u"\n".join(filter(None, [
        default_value if isinstance(default_value, basestring) else None
      ] + list(
        set(
          py_.get(self.data, '%s.%s' % (_field, lang[2]), None) for lang in settings.LANGUAGES)
      )
                                ))
      if value:
        contents.append((value, _weight, 'simple'))

    authors = u", ".join([u'%s' % t.fullname for t in self.authors.all()])
    # well, quite complex.
    tags = u", ".join(set(filter(None, py_.flatten([
      [py_.get(tag.data, 'name.%s' % lang[2], None) for lang in settings.LANGUAGES] + [tag.slug, tag.name] for tag in
      self.tags.only('slug', 'name', 'data')
    ]))))
    # 
    if authors:
      contents.append((authors, 'A', 'simple'))
    if tags:
      contents.append((tags, 'C', 'simple'))

    contents.append((u"\n".join(BeautifulSoup(markdown(u"\n\n".join(filter(None, [
      self.contents,
    ])), extensions=['footnotes'])).findAll(text=True)), 'B', 'simple'))

    q = ' || '.join(
      ["setweight(to_tsvector('simple', COALESCE(%%s,'')), '%s')" % weight for value, weight, _config in contents])

    with connection.cursor() as cursor:
      cursor.execute(''.join(["""
        UPDATE miller_story SET search_vector = x.weighted_tsv FROM (  
          SELECT id,""",
                              q,
                              """
                AS weighted_tsv
            FROM miller_story
          WHERE miller_story.id=%s
        ) AS x
        WHERE x.id = miller_story.id
      """]), [value for value, _w, _c in contents] + [self.id])

    logger.debug('story {pk:%s, slug:%s} search_vector updated.' % (self.pk, self.slug))

    return contents

  # unstore (usually when deleted)
  def unstore(self, ix=None):
    # if settings.TESTING:
    #   logger.debug('mock storing data during test')
    #   return
    if ix is None:
      ix = helpers.get_whoosh_index()

    writer = ix.writer()

    writer.delete_by_term('path', u"%s" % self.short_url)
    # Save the deletion to disk
    writer.commit()

  def remove_git_tag(self, tag):
    print self.get_git_path()

    try:
      repo = Repo.init(settings.GIT_ROOT)
      # repo.delete_tag(tag)
      print repo.git.log('--follow', '--date=iso-strict', '--no-walk', '--tags', '--pretty=%h%d %cd', '--',
                         self.get_git_path())

    except Exception as e:
      if raise_eception:
        raise e
      else:
        logger.exception(e)
    logger.debug('story {pk:%s, version:%s} REMOVED git tag %s' % (self.pk, self.version, tag))

  def gitTag(self, tag, message='', versioned=True, raise_eception=False, author=None):
    """
    Convenient function to handle GIT tagging
    """
    from datetime import datetime
    date_tag_created = datetime.utcnow().isoformat()

    try:
      repo = Repo.init(settings.GIT_ROOT)
      new_tag = repo.create_tag('%s.%s' % (tag, self.version) if versioned else tag,
                                message=u'%sZ - %s - %s' % (date_tag_created, author if author else '', message))
    except Exception as e:
      if raise_eception:
        raise e
      else:
        logger.exception(e)
    logger.debug('story {pk:%s, version:%s} git tagged as %s by %s' % (self.pk, self.version, tag, author))

  def gitLog(self, limit=4, offset=0):
    from django.utils import timezone
    from datetime import datetime
    repo = Repo.init(settings.GIT_ROOT)
    path = self.get_git_path()
    git = repo.git()

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

  def get_git_diff(self, commit_id):
    """
    get git diff from the current version to the commit_id sha1
    """
    path = self.get_git_path()
    repo = Repo.init(settings.GIT_ROOT)
    results = [],
    _r = {};

    # produce:  git diff --no-color --word-diff 68a03a1:users/k8CxmWi/ALAgdn8.md users/k8CxmWi/ALAgdn8.md
    diff = repo.git.diff('--no-color', '--word-diff', '%s:%s' % (commit_id, path), path)

    logger.debug('story {pk:%s} exec: git diff --no-color --word-diff %s:%s %s' % (self.pk, commit_id, path, path))
    # return results
    # diff = repo.git.diff('--unified=0','%s:%s' % (commit_id,path),path)
    results = re.split(r'(@@ \-\d+,?\d* \+\d+,?\d* @@)', diff)

    if results:
      _r['headers'] = results.pop(0);
      _r['diff'] = dict(zip(results[::2], results[1::2]))

    return _r

  def get_git_tags(self):
    from django.utils import timezone, dateparse
    from datetime import datetime

    path = self.get_git_path()
    repo = Repo.init(settings.GIT_ROOT)
    # tags = sorted(repo.tags, key=lambda t: t.commit.committed_date)
    results = []
    logs = repo.git.log('--follow', '--date=iso-strict', '--no-walk', '--tags', '--pretty=%h%d %cd', '--',
                        path).splitlines()

    for l in logs:
      parts = re.match(r'(?P<hexsha>[a-f0-9]+)\s+\((?P<refs>[^\)]*)\)\s+(?P<date>.*)$', l)
      if not parts:
        continue
      _log = {
        'hexsha': parts.group('hexsha'),
        'date': dateparse.parse_datetime(parts.group('date')),
        'tags': []
      }
      # for matching each tag in git log like:
      # ebc38e3 (HEAD -> master, tag: vaz3.0.ebc3, tag: vaz2.0.ebc3, tag: vaz1.0.ebc3, tag: v1.0.ebc3) 2017-06-20T09:40:54+00:00
      for i in re.finditer(r'tag\: (?P<path>[^,]+)', parts.group('refs')):
        _tag = {
          'tag': '.'.join(i.group('path').split('.')[:-1]),
          'message': None,
          'username': None,
          'date': None
        }
        # get tag reference which MAY contain a message,
        ref = repo.tags[i.group('path')]

        if ref.tag:
          parts = re.match(r'^(?P<date>[^\s]*) - (?P<username>[^\s]*) - (?P<message>.*)$', ref.tag.message)
          if not parts:
            _tag['message'] = ref.tag.message
          else:
            _tag.update({
              'date': parts.group('date'),
              'username': parts.group('username'),
              'message': parts.group('message')
            })
        # then append it to the response.
        _log['tags'].append(_tag)
        _log['tags'] = sorted(_log['tags'], key=lambda x: (x['date'],), reverse=True)
      results.append(_log)
    return results

  def get_git_contents_by_commit(self, commit_id):
    repo = Repo.init(settings.GIT_ROOT)
    path = self.get_git_path()
    try:
      file_contents = repo.git.show('%s:%s' % (commit_id, path))
    except Exception as e:
      logger.exception(e)
      return None
    return file_contents

  def get_git_tags_by_commit(self, commit_id):
    repo = Repo.init(settings.GIT_ROOT)
    path = self.get_git_path()
    results = []
    logs = repo.git.tag('-l', '-n1000', '--points-at', commit_id).splitlines()
    for l in logs:
      parts = re.match(r'(?P<tag>[A-Za-z0-9\.\_\-]+)\s+(?P<date>[^\s]*) - (?P<username>[^\s]*) -\s*(?P<message>.*)$', l)
      if not parts:
        continue
      results.append({
        'hexsha': parts.group('tag').split('.')[-1],
        'tag': '.'.join(parts.group('tag').split('.')[:-1]),
        'date': parts.group('date'),
        'username': parts.group('username'),
        'message': parts.group('message')
      })
    return results

  def get_highlights_by_commit(self, commit_id):
    version = commit_id.split('.')[-1]
    return filter(None,
                  self.comments.exclude(status='deleted').filter(version=version).values_list('highlights', flat=True))

  def gitBlob(self, commit_id):
    repo = Repo.init(settings.GIT_ROOT)
    # relative path to repo
    path = self.get_git_path()

    logger.debug('story {pk:%s} git show %s:%s' % (self.pk, commit_id, path))

    try:
      file_contents = repo.git.show('%s:%s' % (commit_id, path))
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
            logger.exception(e)
            raise e

    try:
      f = codecs.open(path, encoding='utf-8', mode='w+')
      f.write(self.contents)
      f.seek(0)
      f.close()
    except Exception as e:
      logger.exception(e)
    else:
      logger.debug('story {pk:%s} contents written in %s.' % (self.pk, path))

  def commit_contents(self, force=False):
    """
    Convenient function to commit the Story contents filepath.
    Internally it makes use of Story `diffs` property
    and check if contents has changed before committing.
    """
    if self.pk and not 'contents' in self.diffs:
      logger.debug('story {pk:%s} commit_contents skipped, nothing new to commit.' % (self.pk))
      return
    logger.debug('story {pk:%s} diffs: %s' % (self.pk, json.dumps(self.diffs)))

    # NOTE: COMMIT needs to be tested for multi-user writing
    # if not force and settings.TESTING:
    #   logger.debug('story {pk:%s} commit_contents git commit skipped, just testing!' % self.pk)
    #   return

    author = Actor(self.owner.username, self.owner.email)
    committer = Actor(settings.GIT_COMMITTER['name'], settings.GIT_COMMITTER['email'])

    # commit if there are any differences
    repo = Repo.init(settings.GIT_ROOT)

    # add and commit JUST THIS FILE
    # tree = Tree(repo=repo, path=self.owner.profile.get_path())
    try:
      repo.index.add([self.get_path()])
      c = repo.index.commit(message=u"saving %s" % self.title, author=author, committer=committer)
      short_sha = repo.git.rev_parse(c, short=7)
    except IOError as e:
      logger.debug('story {pk:%s} gitCommit has errors.' % self.pk)
      logger.exception(e)

    self.version = short_sha
    logger.debug('story {pk:%s} gitCommit {hash:%s,short:%s} done.' % (self.pk, c, short_sha))

  def _generate_output_file_html(self, outputfile):
    # Use pandoc to convert markdown to html
    content = pypandoc.convert_text(self.contents, 'html', format='md')

    cover_image = self.covers.get().url if self.covers.exists() else None

    # Fill the html template
    # TODO(Michael): Set correct langage
    template = get_template('pdf_template.html')
    html = template.render({
      'title': self.title,
      'abstract': self.abstract,
      'activity': 'Project',
      'tags': [t.data['name']['en_US'] for t in self.tags.filter(category=Tag.KEYWORD)],
      'date_last_modified': self.date_last_modified,
      'content': content,
      'authors': ', '.join([u'<b>{}</b>{}'.format(a.fullname, ' ({})'.format(a.affiliation) if a.affiliation else '') for a in self.authors.all()]),
      'cover_image': cover_image
    })

    # Convert html into pdf and write outputfile
    HTML(string=html).write_pdf(target=outputfile)

  def _generate_output_file(self, outputfile, outputFormat):
    tempoutputfile = user_path(self, '__%s.md' % self.short_url)
    logger.debug('story {pk:%s} creating temp file.' % self.pk)
    authors = u", ".join([u'%s' % t.fullname for t in self.authors.all()])
    tags = u",".join([u'%s' % t.slug for t in self.tags.filter(category=Tag.KEYWORD)])

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
                            '-V', 'author=%s' % ', '.join(
                              [u'%s (%s)' % (a.fullname, a.affiliation) for a in self.authors.all()]),
                            '-V', 'keywords=%s' % tags,
                            '-V', 'abstract=%s' % self.abstract.replace('&', '\&') if self.abstract else ''
                          ])
    # once done,
    os.remove(tempoutputfile)

  # convert the last saved content (markdown file) to a specific format (default: docx)
  # the media will be in the user MEDIA folder...
  def download(self, outputFormat='docx', language=None, extension=None, medium='html'):
    outputfile = user_path(self, '%s-%s.%s' % (
      self.short_url,
      self.date_last_modified.strftime("%s"),
      extension if extension is not None else outputFormat
    ), True)

    print '-----------\n{}\n-----------'.format(outputfile)
    # TODO(Michael): To uncomment
    # if os.path.exists(outputfile):
    #   print "do not regenerate", outputfile, self.date_last_modified.strftime("%s")
    #   return outputfile

    if outputFormat == 'pdf' and medium == 'html':
      self._generate_output_file_html(outputfile)
    else:
      self._generate_output_file(outputfile, outputFormat)

    return outputfile

  def send_smart_email(self, recipient, template_name, from_email=settings.DEFAULT_FROM_EMAIL, extra={}):
    if not settings.EMAIL_HOST and not settings.TESTING:
      logger.warning(
        'story {pk:%s} email %s cannot be send, settings.EMAIL_HOST is not set.' % (self.pk, template_name))
      return
    recipient_list = [recipient if isinstance(recipient, basestring) else recipient.email]
    context = {
      'recipient': recipient,
      'story': self,
      'site_name': settings.MILLER_TITLE,
      'site_url': settings.MILLER_SETTINGS['host'],
    }
    context.update(extra)
    try:
      send_templated_mail(template_name=template_name, from_email=from_email, recipient_list=recipient_list,
                          context=context)
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
      logger.debug(
        'story {pk:%s} sending email to DEFAULT_FROM_EMAIL {email:%s}...' % (self.pk, settings.DEFAULT_FROM_EMAIL))
      context = {
        'title': self.title,
        'abstract': self.abstract,
        'slug': self.slug,
        'first_author': self.owner.authorship.first(),
        'username': 'staff member',
        'site_name': settings.MILLER_TITLE,
        'site_url': settings.MILLER_SETTINGS['host']
      }
      if extra:
        context.update(extra)
      send_templated_mail(template_name=template_name, from_email=settings.DEFAULT_FROM_EMAIL,
                          recipient_list=[recipient], context=context)
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
        send_templated_mail(template_name=template_name, from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=recipient, fail_silently=False, context={
            'title': self.title,
            'abstract': self.abstract,
            'slug': self.slug,
            # 'authors':  self.authors.all(),
            'author': author,
            'site_name': settings.MILLER_TITLE,
            'site_url': settings.MILLER_SETTINGS['host']
          })
      except Exception as e:
        logger.exception(e)
    else:
      logger.debug('story {pk:%s} cannot send email to recipient, not found fo author {pk:%s}' % (self.pk, author.pk))

  def create_first_author(self):
    author = self.owner.authorship.first()
    print self.owner.authorship.first(), self.owner.is_superuser
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
        print 'publishedddddd'
        self.gitTag(Story.PUBLIC, author='staff')
        # increase/recalculate authors stories
        for author in self.authors.all():
          author.updatePublishedStories()
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
        # tag as reviewed
        self.gitTag(Story.REVIEW_DONE, author='staff')

        # chief reviewer has closed the review process.
        closingremarks = self.reviews.filter(category='closing').select_related('assignee').first()

        self.send_email_to_staff(template_name='story_reviewdone_for_staff', extra={
          # chief decision:
          'closingremarks': closingremarks,
          'reviews': self.reviews.filter(category='double')
        })
        # send mail to chief reviewer @todo
      elif self.status == Story.PRE_PRINT:
        self.gitTag(Story.PRE_PRINT, author='staff')

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

    # this is the woner
    # print 'owner', self.owner
    # create story file if it is not exists; if the story eists already, cfr the followinf story_ready
    if self._saved == 1:
      try:
        self.write_contents()
        self.commit_contents()
      except Exception as e:
        logger.exception(e)
      else:
        logger.debug('story@save {pk:%s}: write_contents_to_path done.' % self.pk)

    logger.debug(
      'story@save {slug:%s,pk:%s} completed, ready to dispatch @postsave, time=%s' % (self.slug, self.pk, self._saved))
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
  logger.debug('story@pre_save {pk:%s, short_url:%s} cache deleted.' % (instance.pk, instance.short_url))


@receiver(pre_save, sender=Story)
def fill_metadata(sender, instance, **kwargs):
  if 'title' not in instance.data:
    instance.data['title'] = {}
  if 'abstract' not in instance.data:
    instance.data['abstract'] = {}

  for lowercase_language_code, label, language_code, idx in settings.LANGUAGES:
    # LANGUAGES = [
    #   ('fr-fr', _('French'), 'fr_FR', 'french'),
    #   ('de-de', _('German'), 'de_DE', 'german'),
    #   ('en-us', _('US English'), 'en_US', 'english'),
    #   ('en-gb', _('British English'), 'en_GB', 'english'),
    # ]
    if language_code not in instance.data['title']:
      instance.data['title'][language_code] = ''
    if language_code not in instance.data['abstract']:
      instance.data['abstract'][language_code] = ''

  logger.debug('story@pre_save {pk:%s}: metadata ready.' % instance.pk)
  # if getattr(instance, '_dirty', None) is not None:
  #   return
  # try:
  #   metadata = instance.dmetadata
  #   if 'title' not in metadata:
  #     metadata['title'] = {}
  #   if 'abstract' not in metadata:
  #     metadata['abstract'] = {}
  #   for lowercase_language_code, label, language_code, idx in settings.LANGUAGES:
  #     # LANGUAGES = [
  #     #   ('fr-fr', _('French'), 'fr_FR'),
  #     #   ('de-de', _('German'), 'de_DE'),
  #     #   ('en-us', _('US English'), 'en_US'),
  #     #   ('en-gb', _('British English'), 'en_GB'),
  #     # ]
  #     # if lowercase_language_code not in metadata['title']:
  #     #   metadata['title'][lowercase_language_code] = instance.title
  #     # if lowercase_language_code not in metadata['abstract']:
  #     #   metadata['abstract'][lowercase_language_code] = instance.abstract
  #     if language_code not in metadata['title']:
  #       metadata['title'][language_code] = ''
  #     if language_code not in metadata['abstract']:
  #       metadata['abstract'][language_code] = ''
  #   instance.metadata = json.dumps(metadata, ensure_ascii=False, indent=1)
  # except Exception as e:
  #   logger.exception(e)
  # else:
  #   logger.debug('story@pre_save {pk:%s}: metadata ready.' % instance.pk)


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

  logger.debug('story@post_save {pk:%s}' % instance.pk)

  from miller.tasks import story_update_search_vectors

  story_update_search_vectors.delay(instance.pk)
  # always store in whoosh.
  # instance.store()


# clean store in whoosh when deleted
# DEPRECATED
# @receiver(pre_delete, sender=Story)
# def unstore_working_md(sender, instance, **kwargs):
#   instance.unstore()
#   logger.debug('story@pre_delete {pk:%s} unstore_working_md: done' % instance.pk)


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

  # if settings.TESTING:
  #   logger.debug('story@pre_delete {pk:%s} delete_working_md skipped commit, just testing!' % instance.pk)
  #   return

  # commit if there are any differences
  repo = Repo.init(settings.GIT_ROOT)

  # add and commit JUST THIS FILE
  # tree = Tree(repo=repo, path=instance.owner.profile.get_path())
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
    # instance.store(receiver='m2m_changed tags')
    ckey = 'story.%s' % instance.short_url
    cache.delete(ckey)
    cache.delete('story.featured')


@receiver(m2m_changed, sender=Story.covers.through)
def store_covers(sender, instance, **kwargs):
  if kwargs['action'] == 'post_add' or kwargs['action'] == 'post_remove':
    ckey = 'story.%s' % instance.short_url
    cache.delete(ckey)


@receiver(m2m_changed, sender=Story.authors.through)
def store_authors(sender, instance, **kwargs):
  if kwargs['action'] == 'post_add' or kwargs['action'] == 'post_remove':
    # instance.store(receiver='m2m_changed authors')
    ckey = 'story.%s' % instance.short_url
    cache.delete(ckey)
