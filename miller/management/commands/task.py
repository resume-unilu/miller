#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Tasks on models
import os, logging, json, re, requests, StringIO, datetime, time

from miller.helpers import get_whoosh_index
from miller.models import Author, Document, Story, Profile, Tag
from miller.management.commands import utils

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.db import transaction


logger = logging.getLogger('console')



class Command(BaseCommand):
  """
  Usage sample: 
  python manage.py task snapshot --pk=991
  """
  help = 'Initialize the JSON field metadata for Story instances'
  

  available_tasks = (
    'noembed',
    'snapshot', # require document pk, e.g python manage.py task snapshot --pk=991
    'snapshots', # handle pdf snapshot, python manage.py task snapshots
    'snapshots404',
    'cleanbin',
    'clean_cache',
    'update_ngrams_table',
    'update_whoosh',
    'update_search_vectors',
    'update_localisation',
    'update_localisation_gs',
    'bulk_import_gs_as_documents',
    'bulk_import_public_gs_as_documents',
    'bulk_import_gs_as_tags',
    'bulk_import_gs_as_biographies',
    # tasks migration related.
    'migrate_documents',
    'migrate_stories',
    'migrate_authors'
  )


  def add_arguments(self, parser):
    parser.add_argument('taskname')
    # Named (optional) arguments
    parser.add_argument(
        '--pk',
        dest='pk',
        default=None,
        help='primary key of the instance',
    )

    parser.add_argument(
        '--model',
        dest='model',
        default=False,
        help='miller model name',
    )

    parser.add_argument(
        '--url',
        dest='url',
        default=False,
        help='google spreadsheet url',
    )

    parser.add_argument(
        '--sheet',
        dest='sheet',
        default=False,
        help='google spreadsheet url sheeet name',
    )

    parser.add_argument(
        '--gsid',
        dest='gsid',
        default=False,
        help='google spreadsheet ID',
    )

    parser.add_argument(
        '--gid',
        dest='gid',
        default=False,
        help='google spreadsheet sheet ID',
    )


    parser.add_argument(
        '--cache',
        dest='cache',
        default=False,
        help='enable redis caching for offline jobs',
    )

    parser.add_argument(
        '--owner',
        dest='owner',
        default=False,
        help='miller username',
    )


  def handle(self, *args, **options):
    start = time.time()
    if options['taskname'] in self.available_tasks:
      getattr(self, options['taskname'])(**options)
    else:
      logger.debug('command NOT FOUND, tasks availables: ["%s"]' % '","'.join(self.available_tasks))
    end = time.time()
    logger.debug('command finished in %s seconds.' % (end - start))
  
  
  


  def migrate_documents(self, **options):
    logger.debug('task: migrate_documents')
    docs = Document.objects.filter(data={})
    
    for doc in docs.iterator():
      logger.debug('task: migrate_documents for document {pk:%s}' % doc.pk)
      d = doc.dmetadata
      d.update({})
      doc.data = d
      doc.save()

  def migrate_stories(self, **options):
    logger.debug('task: migrate_stories')
    stories = Story.objects.filter(data={})
    
    logger.debug('task: migrate_stories for %s stories with empty data' % stories.count())
    for story in stories.iterator():
      logger.debug('task: migrate_stories for document {pk:%s}' % story.pk)
      d = story.dmetadata
      d.update({})
      story.data = d
      story.save()


  def migrate_authors(self, **options):
    logger.debug('task: migrate_authors')
    authors = Author.objects.all()
    
    for author in authors.iterator():
      logger.debug('task: migrate_authors for authorument {pk:%s}' % author.pk)
      d = author.dmetadata
      d.update({})
      author.data = d
      author.updatePublishedStories()
      # count!
      #author.data['num_publication'] = Story.objects.filter(status=PUBLIC)
      author.save()


  def clean_cache(self, **options):
    logger.debug('task: clean_cache')
    from django.core.cache import cache
    cache.clear();

  
  def bulk_import_gs_as_documents(self, url=None, sheet=None, use_cache=False, **options):
    if not url:
      raise Exception('please specify a google spreadsheet url with the --url parameter')

    logger.debug('loading %s' % url)

    rows, headers = utils.bulk_import_gs(url=url, sheet=sheet, use_cache=use_cache, required_headers=['slug', 'type'])
    
    # owner is the first staff user
    owner = Profile.objects.filter(user__is_staff=True).first()

    if not owner:
      raise Exception('no Profile object defined in the database!')

    data_paths =  utils.data_paths(headers=headers) 
    print data_paths
    # basic data structure based on headers column
    data_structure = {}

    for i, path, is_list in data_paths:
      utils.nested_set(data_structure, path, {})

    logger.debug('data__* fields have been transformed to: %s' % data_structure)

    for i, row in enumerate(rows):
      if not row['slug'] or not row['type']:
        logger.debug('line %s: empty "slug" or empty "type", skipping.' % i)
        continue
      _slug = row['slug'].strip()
      _type = row['type'].strip()

      doc, created = Document.objects.get_or_create(slug=_slug, type=_type, defaults={
        'owner': owner.user
      })
      doc.title = row['title'].strip()

      _data = data_structure.copy()
      
      for key, path, is_list in data_paths:
        utils.nested_set(_data, path, row[key], as_list=is_list)
      
      doc.data.update(_data['data'])
      # print doc.data
      if 'attachment' in row and len(row['attachment'].strip()) > 0:
         doc.attachment.name = row['attachment']

      doc.save()
      logger.debug('line %(line)s: document created {pk:%(pk)s, type:%(type)s, slug:%(slug)s, created:%(created)s}' % {
        'line': i,
        'slug': _slug,
        'type': _type,
        'pk': doc.pk,
        'created': created
      })


  def bulk_import_public_gs_as_documents(self, gsid=False, gid=False, use_cache=False, **options):
    if not gsid:
      if not settings.MILLER_DOCUMENTS_GOOGLE_SPREADSHEET_ID:
        raise Exception('please specify a google spreadsheet url with the --url parameter')
      else:
        gsid = settings.MILLER_DOCUMENTS_GOOGLE_SPREADSHEET_ID

    logger.debug('GSID %s' % gsid)
    rows, headers = utils.bulk_import_public_gs(gsid=gsid, gid=gid, use_cache=use_cache, required_headers=['slug', 'type']);

    owner = Profile.objects.filter(user__is_staff=True).first()

    if not owner:
      raise Exception('no Profile object defined in the database!')

    data_paths =  utils.data_paths(headers=headers) 
    print data_paths

    

    # basic data structure based on headers column
    data_structure = {}

    for i, path, is_list in data_paths:
      utils.nested_set(data_structure, path, {})

    logger.debug('data__* fields have been transformed to: %s' % data_structure)

    
      

    for i, row in enumerate(rows):
      if not row.get('slug') or not row.get('type'):
        logger.debug('line %s: empty "slug" or empty "type", skipping.' % i)
        continue

      _slug = row['slug'].strip()
      _type = row['type'].strip()
      _docs = row.get('related_documents|list', '').split(',')
      _has_attachment = 'attachment' in row and row['attachment'] and len(row['attachment'].strip()) > 0
      _has_snapshot = 'snapshot' in row and row['snapshot'] and len(row['snapshot'].strip()) > 0

      # read just one line of the CSV
      if 'pk' in options and options.get('pk') is not None and options.get('pk') != row['slug']:
        continue
      
      # Document model fields
      if 'attachment' in row:
        if not row['attachment']:
          if 'url' in row and not row['url']:
            logger.warning('line {0}: empty "attachment" and empty "url" when "attachment" is in header, skipping for {1}.'.format(i, _slug))
            continue
          elif not 'url' in row:
            logger.warning('line {0}: empty "attachment", but "attachment" is in header, skipping for {1}.'.format(i, _slug))
            continue

      if 'date__year' in row and not row['date__year']:
        logger.warning('line {0}: empty "date__year" and empty "url" when "attachment" is in header, skipping for {1}.'.format(i, _slug))
        continue
      
      if _has_snapshot:
        logger.debug('line {line}: found snapshot for {slug}, {snapshot}'.format(line=i, slug=_slug, snapshot=row['snapshot']))

        _snapshot_path      = row['snapshot'].strip()
        _snapshot_abspath = os.path.join(settings.MEDIA_ROOT, _snapshot_path)
        _snapshot_exists  = os.path.exists(_snapshot_abspath)

      if _has_attachment: 
        _attachment_path    = row['attachment'].strip()
        _attachment_abspath = os.path.join(settings.MEDIA_ROOT, _attachment_path)
        _attachment_exists  = os.path.exists(_attachment_abspath)
        # logger.debug(u'line {0}: attachment found, \n   - datum: {1}\n   - real: {2}\n   exists: {3}'.format(i, row['attachment'], _attachment_abspath, _attachment_exists))
        # check that the file exists; otherwise skip everything
        if not _attachment_exists:
          logger.warning('line %s: no real path has been found for the attachment, skipping.' % i)
          continue


      



      doc, created = Document.objects.get_or_create(slug=_slug, type=_type, defaults={
        'owner': owner.user
      })
      doc.title = row['title'].strip()

      _data = data_structure.copy()
      
      

      for key, path, is_list in data_paths:
        utils.nested_set(_data, path, row[key], as_list=is_list)
      

      # Clean data structure
      if 'place_type' in _data['data'] and 'coordinates' in _data['data'] and not row['data__place_type']:
        logger.debug('line {0}: clean data.coordinates from data_paths for {1}'.format(i, _slug))
        _data['data'].pop('coordinates', None)

      doc.data = _data['data']

      if 'url' in row and len(row['url'].strip()) > 0:
        doc.url = row['url'].strip()
        doc.fill_from_url()

      # print doc.data
      if _has_snapshot:
        # check that the file exists; otherwise skip everything
        logger.debug(u'line {0}: assign snapshot: {1}'.format(i, _snapshot_path))
        doc.snapshot.name = _snapshot_path

      if _has_attachment:
        # check that the file exists; otherwise skip everything
        logger.debug(u'line {0}: assign attachment: {1}'.format(i, _attachment_path))
        doc.attachment.name = _attachment_abspath

      if _has_attachment or _has_snapshot:
        # create snapshots
        doc.create_snapshots(custom_logger=logger)

      doc.save()

      
      logger.debug('line {line}: document {created}, pk={pk}, type={type}, slug={slug}.'.format(line= i,slug= _slug, type= _type,
        pk= doc.pk,
        created= 'CREATED' if created else 'UPDATED'
      ))

    # add related documents!!!
    if 'related_documents|list' in row:
      for i, row in enumerate(rows):
        _docs = filter(None, row.get('related_documents|list', '').split(','))
        if not _docs or not row.get('slug') or not row.get('type'):
          continue

        _slug = row['slug'].strip()
        _type = row['type'].strip()

        logger.debug('line {0}: document {1} need to be connected to: {2}'.format(i, _slug, _docs))
      
        doc = Document.objects.get(slug=_slug)
        related = Document.objects.filter(slug__in=_docs)
        doc.documents.clear()
        doc.documents.add(*related)
        doc.save()
        logger.debug('line {0}: document {1} connected to: {2}'.format(i, _slug,[d.slug for d in doc.documents.all()]))
        


  def bulk_import_gs_as_tags(self, url=None, sheet=None, use_cache=False, **options):
    if not url:
      raise Exception('please specify a google spreadsheet url with the --url parameter')

    logger.debug('loading %s' % url)

    rows, headers = utils.bulk_import_gs(url=url, sheet=sheet, use_cache=use_cache, required_headers=['slug', 'category', 'data__provider'])
    
    data_paths =  utils.data_paths(headers=headers) 
    data_structure = {}

    for i, path, is_list in data_paths:
      utils.nested_set(data_structure, path, {})

    logger.debug('data__* fields have been transformed to: %s' % data_structure)

    CATEGORIES = [item[0] for item in Tag.CATEGORY_CHOICES]
    logger.debug('categories available: %s' % CATEGORIES)

    for i, row in enumerate(rows):
      if not row['slug'] :
        logger.debug('line %s: empty "slug", skipping.' % i)
        continue


      if not row['category'] or not row['category'] in  CATEGORIES:
        logger.debug('line %s: category "%s" not matching %s, skipping.' % (i, row['category'], CATEGORIES))
        continue

      _category = row['category'].strip()

      _slug = row['slug'].strip()

      if len(_slug) > 100:
        logger.debug('line %s: "slug" length is excessive, BREAK!' % i)
        break;

      # this will raise an error if the tag exists already (changing category is not permitted here)
      tag, created = Tag.objects.get_or_create(slug=_slug, category=_category)

      tag.name = row.get('name', '').strip()


      _data = data_structure.copy()
      
      for key, path, is_list in data_paths:
        utils.nested_set(_data, path, row[key], as_list=is_list)
      
      tag.data = _data['data']
      logger.debug('tag saved {slug:%s, created:%s, name:%s}' % (tag.slug, created, tag.name))
      tag.save()

    #with transaction.atomic():  
      
    #     for row in r:
    #       tag, created = Tag.objects.get_or_create(category=Tag.KEYWORD, name=row['name'],slug=row['slug']);
    #       print created, tag

  def update_localisation_gs(self,  **options):
    """ 
    load the csv specified in MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET, if any provided.
    """
    url = settings.MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET
    # something like https://docs.google.com/spreadsheets/d/{yourid}/edit#gid=0
    if not url:
      raise Exception('no google spreadsheet link in settings.MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET')
    
    #print url

    m = re.match(r'https://docs.google.com/spreadsheets/d/([^/]*)', url)
    if not m:
      raise Exception('bad url in settings.MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET')
    import requests, StringIO
    response = requests.get('https://docs.google.com/spreadsheets/d/%s/export?format=csv' % m.group(1), stream=True)
    print response.encoding
    response.encoding = 'utf8'
    # print response.content
    # rows = csv.DictReader(StringIO.StringIO(response.content), encoding='utf-8', delimiter='\t')
    if response.status_code != 200:
      raise Exception('bad response for settings.MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET')
    # for row in rows:
    #   print row
    logger.debug('writing csv file at settings.MILLER_LOCALISATION_TABLE:%s', settings.MILLER_LOCALISATION_TABLE)
    with open(settings.MILLER_LOCALISATION_TABLE, 'wb') as f:
      for chunk in response.iter_content(chunk_size=1024): 
        if chunk: # filter out keep-alive new chunks
          f.write(chunk)
    
    logger.debug('now updating localisation...')
    self.update_localisation(**options)


  def update_localisation(self,  **options):
    """ 
    load the csv specified in MILLER_LOCALISATION_TABLE
    """
    logger.debug('looking for the csv file at settings.MILLER_LOCALISATION_TABLE: %s'%settings.MILLER_LOCALISATION_TABLE)
    import unicodecsv as csv
    
    with open(settings.MILLER_LOCALISATION_TABLE) as f:
      rows = csv.DictReader(f, encoding='utf-8')
      translations = {}
      for row in rows:
        for lang, t, language_code, idx in settings.LANGUAGES:
          if not language_code in translations:
            translations[language_code] = {}
          
          translations[language_code].update({
            row[u'KEY']: row[u'en_US'] if not row[language_code] else row[language_code]
          })
      #print translations
      for language_code, value in translations.iteritems():
        print language_code
        localename = os.path.join(os.path.dirname(settings.MILLER_LOCALISATION_TABLE), 'locale-%s.json' % language_code)
          
        with open(localename, "w") as wtf:
          logger.debug('creating: %s'%localename)
          wtf.write(json.dumps(translations[language_code],indent=2))

            #print row
    pass

  def update_whoosh(self,  **options):
    logger.debug('looking for a whoosh index...')
    ix = get_whoosh_index(force_create=True)

    _model = options.get('model', None)
    logger.debug('whoosh index for --model: %s...'% _model)
    
    if _model == 'story':
      stories = Story.objects.filter(pk=options.get('pk')) if options.get('pk', None) is not None else Story.objects.all()
      print  options.get('pk', None)
      logger.debug('stories: %s' % stories.count())

      # # The `iterator()` method ensures only a few rows are fetched from
      # # the database at a time, saving memory.
      for story in stories.iterator():
        logger.debug('task: update_whoosh for story {pk:%s}' % story.pk)
        try:
          story.store(ix=ix)
        except Exception as e:
          logger.exception(e)
          break
        else:
          logger.debug('task: update_whoosh for story {pk:%s} success' % story.pk)
      
    elif _model == 'document':
      docs =  Document.objects.filter(pk=options.get('pk')) if options.get('pk', None) is not None else Document.objects.all()

      # The `iterator()` method ensures only a few rows are fetched from
      # the database at a time, saving memory.
      for doc in docs.iterator():
        logger.debug('task: update_whoosh for doc {pk:%s}...' % doc.pk)
        try:
          doc.store(ix=ix)
        except Exception as e:
          logger.exception(e)
          break
        else:
          logger.debug('task: update_whoosh for doc {pk:%s} success' % doc.pk)
    else:
      logger.debug('task: please provide a valid model to update_whoosh: "document" or "story"...')
        

  def noembed(self, **options):
    logger.debug('task: noembed!')
    if not options['pk']:
      raise Exception('--pk not found')
    
    logger.debug('task: noembed for {document:%s}' % options['pk'])

    doc = Document.objects.get(pk=options['pk'])
    try:
      doc.noembed()
      doc.save()
    except Exception as e:
      logger.exception(e)


  def snapshot(self, **options):
    logger.debug('task: snapshot!')
    if not options['pk']:
      raise Exception('--pk not found')
    
    logger.debug('task: snapshot for {document:%s}' % options['pk'])

    doc = Document.objects.get(pk=options['pk'])
    try:
      doc.fill_from_url()
      doc.create_snapshot()
      doc.save()
    except Exception as e:
      logger.exception(e)

  def snapshots(self, **options):
    logger.debug('task: snapshots!')

    docs = Document.objects.all()

    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for doc in docs.iterator():
      logger.debug('task: snapshots for {document:%s}' % doc.id)
      try:
        doc.fill_from_url()
        doc.create_snapshot()
        doc.save()
      except Exception as e:
        logger.exception(e)


  def snapshots404(self, **options):
    """
    Find snapshots giving 404 so that we know what need to be fixed.
    """
    logger.debug('task: find 404 snapshots!')

    docs = Document.objects.exclude(url__isnull=True).filter(mimetype='application/pdf')
    logger.debug('  looking for application/pdf on %s / %s documents.' % (docs.count(), Document.objects.all().count()))
    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for doc in docs.iterator():
      if not doc.snapshot or not os.path.exists(doc.snapshot.path):
        logger.debug('task: snapshot missing for {document:%s}' % doc.id)
      # try:
      #   doc.fill_from_url()
      #   doc.create_snapshot()
      #   doc.save()
      # except Exception as e:
      #   logger.exception(e)

    # having snapshot. Do file exists?
    # docs = Document.objects.exclude(snapshot__isnull=True)
    # for doc in docs.iterator():
    #   os.path.exists(doc.snapshot.path)

  #cleaning story.DELETED older than 2 months
  def cleanbin(self, **options):
    logger.debug('task: cleanbin')
      
