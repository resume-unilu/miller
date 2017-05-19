#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Tasks on models
import os, logging, json, re, requests, StringIO, datetime

from miller.helpers import get_whoosh_index
from miller.models import Author, Document, Story, Profile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache

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
    'update_whoosh',
    'update_localisation',
    'update_localisation_gs',
    'bulk_import_gs_as_documents',
    # tasks migration related.
    'migrate_documents',
    'migrate_authors'
  )


  def add_arguments(self, parser):
    parser.add_argument('taskname')
    # Named (optional) arguments
    parser.add_argument(
        '--pk',
        dest='pk',
        default=False,
        help='primary key of the instance',
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
        '--cache',
        dest='cache',
        default=False,
        help='enable redis caching for offline jobs',
    )


  def handle(self, *args, **options):
    if options['taskname'] in self.available_tasks:
      getattr(self, options['taskname'])(**options)
    else:
      logger.debug('command NOT FOUND, tasks availables: ["%s"]' % '","'.join(self.available_tasks))
    logger.debug('command finished.')
  
  
  def migrate_documents(self, **options):
    logger.debug('task: migrate_documents')
    docs = Document.objects.filter(data={})
    
    for doc in docs.iterator():
      logger.debug('task: migrate_documents for document {pk:%s}' % doc.pk)
      d = doc.dmetadata
      d.update({})
      doc.data = d
      doc.save()


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


  def bulk_import_gs_as_documents(self,  **options):
    if not 'url' in options:
      raise Exception('no google spreadsheet link. Please pass a valid --url option')

    if not 'sheet' in options:
      raise Exception('please provide the sheet to load')

    logger.debug('using cache: %s' % options['cache'])
    

    url   = options['url']
    sheet = options['sheet']

    m = re.match(r'https://docs.google.com/spreadsheets/d/([^/]*)', url)
    if not m:
      raise Exception('bad url! Must meet the https://docs.google.com/spreadsheets/d/ format and it should be reachable by link')

    key  = m.group(1)
    ckey = 'gs:%s:%s' % (key,sheet)

    

    if options['cache'] and cache.has_key(ckey):
      #print 'serve cahced', ckey
      logger.debug('getting csv from cache: %s' % ckey)
      contents = json.loads(cache.get(ckey))
    else:
      logger.debug('getting csv from https://docs.google.com/spreadsheets/d/%(key)s/gviz/tq?tqx=out:csv&sheet=%(sheet)s' % {
        'key': key, 
        'sheet': sheet
      })
      response = requests.get('https://docs.google.com/spreadsheets/d/%s/gviz/tq?tqx=out:json&sheet=%s' % (key, sheet), stream=True)
      response.encoding = 'utf8'
      m = re.search(r'google\.visualization\.Query\.setResponse\((.*)\)[^\)]*$', response.content);
      cache.set(ckey, m.group(1), timeout=None)
      contents = json.loads(m.group(1))

    

    # _headers = contents['table']['cols'][0] if contents['table']['cols'][0]["label"] else contents['table']['rows'][0]['c'] 
    has_headers_in_cols = len(contents['table']['cols'][0]["label"].strip()) > 0 
    headers = map(lambda x:x[u'label'] if type(x) is dict else None, contents['table']['cols']) if has_headers_in_cols else map(lambda x:x[u'v'] if type(x) is dict else None, contents['table']['rows'][0]['c'] );
    logger.debug('headers: %s' % headers)
    
    numrows = len(contents['table']['rows']);
    rows = []

    if not 'slug' in headers or not 'type' in headers:
      raise Exception('the first row of the google spreadsheet should be dedicated to headers. This script looks for at least two columns named "slug" and type respectively that have not been found. Go back here once done :D')

    for i in range(0 if has_headers_in_cols else 1, numrows):
      

      row = map(lambda x:x[u'v'] if type(x) is dict else None, contents['table']['rows'][i]['c'])
      rows.append(dict(filter(lambda x:x[0] is not None, zip(headers, row))))
    
    # owner is the first staff user
    owner = Profile.objects.filter(user__is_staff=True).first()

    if not owner:
      raise Exception('no Profile object defined in the database!')

    data_paths =  [(x, x.split('|')[0].split('__'), x.split('|')[-1] == 'list') for x in filter(lambda x: isinstance(x, basestring) and x.startswith('data__'), headers)]

    # basic data structure based on headers column
    data_structure = {}
    

    def nested_set(dic, keys, value, as_list=False):
      for key in keys[:-1]:
        dic = dic.setdefault(key, {})
      if not as_list:
        if not value:
          dic[keys[-1]] = None
        elif keys[-1] in ('start_date', 'end_date'):
          m = re.search(r'(^Date\(?)(\d{4})[,\-](\d{1,2})[,\-](\d{1,2})\)', value)
          if m is not None:
            if m.group(1) is not None:
              # this makes use of Date(1917,4,21) google spreadsheet dateformat.
              # also note that month 4 is not April but is May (wtf)
              logger.debug('parsing date field: %s, value: %s' % (keys[-1],value))
              dic[keys[-1]] = datetime.datetime(year=int(m.group(2)), month=int(m.group(3)) + 1, day=int(m.group(4))).isoformat()
            else:
              # 0 padded values, 1917-05-21
              dic[keys[-1]] = datetime.datetime.strptime('%s-%s-%s' % (m.group(2), m.group(3), m.group(4)), '%Y-%M-%d').isoformat()
          else:
            dic[keys[-1]] = value
        else:
          dic[keys[-1]] = value
      else:
        # it is a list, comma separated ;)
        dic[keys[-1]] = map(lambda x:x.strip(), filter(None, [] if not value else value.split(',')))


    for i, path, is_list in data_paths:
      nested_set(data_structure, path, {})

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
        nested_set(_data, path, row[key], as_list=is_list)
      
      doc.data = _data['data']
      
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




  def update_localisation_gs(self,  **options):
    """ 
    load the csv specified in MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET, if any provided.
    """
    url = settings.MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET
    # something like https://docs.google.com/spreadsheets/d/{yourid}/edit#gid=0
    if not url:
      raise Exception('no google spreadsheet link in settings.MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET')
    
    print url

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
        for lang, t, language_code in settings.LANGUAGES:
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
    logger.debug('looking for a whoosh index')
    ix = get_whoosh_index(force_create=True)
    logger.debug('whoosh index available! Updating ...')
    
    stories = Story.objects.all()

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
      

    docs = Document.objects.all()

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
      
