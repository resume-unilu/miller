#!/usr/bin/env python
# -*- coding: utf-8 -*-
# utils
import os, re, logging, requests, json, datetime
from django.core.cache import cache

logger = logging.getLogger('console')

from django.conf import settings

def dbpedia(wiki_id, use_cache=True):
  """
  Return dbpedia info about the resource
  """
  if not wiki_id:
    print wiki_id
    raise Exception('dbpedia wiki_id should be a valid string, none received.')

  ckey = 'dbpedia:%s' % wiki_id
  logger.debug('dbpedia: loading contents for {wiki_id:%s, url: https://dbpedia.org/data/%s.json}' % (wiki_id, wiki_id))

  if use_cache and cache.has_key(ckey):
    logger.debug('dbpedia: returning cached contents.')
    return json.loads(cache.get(ckey))

  # perform the resuestto dbpedia json endpoint
  res = requests.get('https://dbpedia.org/data/%s.json' % wiki_id)
  res.raise_for_status()

  contents  = res.json()

  if use_cache:
    cache.set(ckey, res.text, timeout=None)


  logger.debug('dbpedia: {status_code:%s, wiki_id:%s}, url: https://dbpedia.org/data/%s.json' % (res.status_code, wiki_id, wiki_id))

  return contents


def data_paths(headers):
  """
  rebuild the structure of data JSON onject based on __ concatenation of headers
  """
  return [(x, x.split('|')[0].split('__'), x.split('|')[-1] == 'list') for x in filter(lambda x: isinstance(x, basestring) and x.startswith('data__'), headers)]


def get_data_from_dict(obj):
  headers = obj.keys()
  # print(headers, obj)
  dp = data_paths(headers=headers)
  data = {}

  # for i, path, is_list in dp:
  #   nested_set(data, path, {})
  # print('data', data)
  for key, path, is_list in dp:
    nested_set(data, path, obj[key], as_list=is_list)
  return data


def get_public_gs_contents(gsid, gid=None, single=False, output='csv'):
    """
    given a google spreadsheet id "published to the web", request the csv contents
    """
    url = 'https://docs.google.com/spreadsheets/d/e/{0}/pub?output=csv'.format(gsid)

    params = {
      'gid': gid,
      'output': output
    }

    response = requests.get(url, stream=True, params=params)
    response.encoding = 'utf8'
    # print response.status_code
    if response.status_code != 200:
      raise Exception('bad response {0} for current url {1}'.format(response.status_code, url))

    return response.content


def bulk_import_public_gs(gsid, gid, use_cache=True, required_headers=['slug']):
  # if not 'sheet':
  url = 'https://docs.google.com/spreadsheets/d/e/{0}/pub'.format(gsid)
  print url, gsid, gid
  ckey = 'gs:%s:%s' % (gsid, gid)
  print ckey

  if use_cache and cache.has_key(ckey):
    #print 'serve cahced', ckey
    logger.debug('getting csv from cache: %s' % ckey)
    contents = cache.get(ckey)
  else:
    logger.debug('loading csv...%s'%url)

    #   raise Exception('please provide the sheet to load')
    response = requests.get(url, stream=True, params={
      'gid': gid,
      'single': 'true',
      'output': 'csv'
    })

    response.encoding = 'utf8'
    contents = response.content
    print 'done'
    cache.set(ckey, contents, timeout=None)

  import csv
  reader = csv.DictReader(contents.splitlines(), delimiter=',')

  return [row for row in reader], reader.fieldnames


def bulk_import_gs(url, sheet, use_cache=True, required_headers=['slug']):
  """
  return rows and headers from the CSV representation of a google spreadsheet.
  This requires:

  url   = options['url']
  sheet = options['sheet']

  """
  if not 'url':
    raise Exception('no google spreadsheet link. Please pass a valid --url option')

  if not 'sheet':
    raise Exception('please provide the sheet to load')

  logger.debug('using cache: %s' % use_cache)

  m = re.match(r'https://docs.google.com/spreadsheets/d/([^/]*)', url)
  if not m:
    raise Exception('bad url! Must meet the https://docs.google.com/spreadsheets/d/ format and it should be reachable by link')

  key  = m.group(1)
  ckey = 'gs:%s:%s' % (key,sheet)

  if use_cache and cache.has_key(ckey):
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
    try:
      cache.set(ckey, m.group(1), timeout=None)
      contents = json.loads(m.group(1))
    except Exception as e:
      logger.debug('cannot find contents... Did you share the google spreadsheet as viewable LINK?')
      raise e


  # _headers = contents['table']['cols'][0] if contents['table']['cols'][0]["label"] else contents['table']['rows'][0]['c']
  has_headers_in_cols = len(contents['table']['cols'][0]["label"].strip()) > 0
  headers = map(lambda x:x[u'label'] if type(x) is dict else None, contents['table']['cols']) if has_headers_in_cols else map(lambda x:x[u'v'] if type(x) is dict else None, contents['table']['rows'][0]['c'] );
  logger.debug('headers: %s' % headers)

  numrows = len(contents['table']['rows']);
  rows = []
  # deis
  if bool(set(required_headers) - set(headers)):
    raise Exception('the first row of the google spreadsheet should be dedicated to headers. This script looks for at least two columns named [%s] that have not been found. Go back here once done :D' % ','.join(required_headers))

  for i in range(0 if has_headers_in_cols else 1, numrows):


    row = map(lambda x:x[u'v'] if type(x) is dict else None, contents['table']['rows'][i]['c'])
    rows.append(dict(filter(lambda x:x[0] is not None, zip(headers, row))))

  return rows, headers

def to_media_url(dir, filepath):
  """
  Retrun media related filepath
  """
  return '{host}{file}'.format(
    host = settings.MILLER_HOST,
    file = os.path.join(settings.MEDIA_URL, dir, filepath)
  )

def get_dirlist(dirpath, media_url, types):
  """
  return a list of filenames by extension

  Parameters
  ----------
  dirpath: str
    existing dirpath location (absolute)
  types: tuple
    is a tuple of `("extension", "mimetype")` tuples

  """
  logger.info('get_dirlist of: {0}'.format(dirpath))

  if not os.path.isdir(dirpath):
    raise TypeError('\'dirpath\' should be a real dir path...!')
  l = []
  for filepath in os.listdir(dirpath):
    ext = filepath.split('.')[-1]
    mimetypes = [item[1] for item in types if item[0] == ext]

    l.append({
      'src': to_media_url(dir=media_url, filepath=filepath),
      'type': mimetypes[0] if mimetypes else None
    })
  return l


def nested_set(dic, keys, value, as_list=False):
  for key in keys[:-1]:
    dic = dic.setdefault(key, {})
  if dic is None:
    raise ValueError('key "{0}" is not a valid dict! Checking "{1}"'.format(key, u'__'.join(keys)))
  if not as_list:
    if isinstance(value, bool):
      dic[keys[-1]] = value
    elif not value:
      dic[keys[-1]] = None
    elif keys[-1] in ('start_date', 'end_date'):
      # print('nested:', keys[-1], value)
      if isinstance(value, basestring):
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
          logger.debug('parsing digit date field: %s, value: %s' % (keys[-1],value))
          dic[keys[-1]] = value
      else:
        dic[keys[-1]] = value
    else:
      dic[keys[-1]] = value
  else:
    # it is a list, comma separated ;)
    dic[keys[-1]] = map(lambda x:x.strip(), filter(None, [] if not value else value.split(',')))
