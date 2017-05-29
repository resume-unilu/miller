#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shortuuid, os, json, logging, mimetypes

from django.conf import settings
from django.http import StreamingHttpResponse
from django.utils.text import slugify
from pyzotero import zotero

from wsgiref.util import FileWrapper


logger = logging.getLogger('miller')



def streamHttpResponse(filename):
  """
  Given an existing filename, 
  """
  mimetype    = mimetypes.guess_type(filename)[0]
  response = StreamingHttpResponse(FileWrapper(open(filename), 8192), content_type=mimetype)
  response['Content-Length'] = os.path.getsize(filename)
  return response



def generate_snapshot(filename, output, width=settings.MILLER_SNAPSHOT_WIDTH, height=settings.MILLER_SNAPSHOT_HEIGHT):
  """
  Use liquid_rescale to scale down snapshots to the desired dimension
  """
  from wand.image import Image
  
  # clean
  try:
    os.remove(output)
  except OSError as e:
    pass

  try:
    os.makedirs(os.path.dirname(output))
  except OSError:
    pass

  d = {}

  if not width and not height:
    raise Exception('At least one dimension should be provided, width OR height')

  with Image(filename=filename) as img:
    ratio = 1.0*img.width/img.height
    d['width']  = img.width
    d['height'] = img.height

    # resize to the minimum, then crop
    if not height:
      height = width / ratio

    if not width:
      width = ratio*height

    if img.width > img.height :
      # width greated than height
      img.transform(resize='x%s'%width)
    elif img.width < img.height:
      img.transform(resize='%sx'%width)
    else:
      img.transform(resize='%sx%s'% (width, height))


    d['thumbnail_width']  = img.width
    d['thumbnail_height'] = img.height
    
    img.crop(width=img.width, height=img.height, gravity='center')

    
    img.save(filename=output)
    return d      
        


def get_previous_and_next(iterable):
  """
  Get previous and next values inside a loop.
  Thanks to http://stackoverflow.com/users/125801/unode and http://stackoverflow.com/users/17160/nosklo
  http://stackoverflow.com/questions/1011938/python-previous-and-next-values-inside-a-loop

  Then use it in a loop, and you'll have previous and next items in it:

  ```
  mylist = ['banana', 'orange', 'apple', 'kiwi', 'tomato']

  for previous, item, nxt in get_previous_and_next(mylist):
    print "Item is now", item, "next is", nxt, "previous is", previous
  ```
  The results:

  Item is now banana next is orange previous is None
  Item is now orange next is apple previous is banana
  Item is now apple next is kiwi previous is orange
  Item is now kiwi next is tomato previous is apple
  Item is now tomato next is None previous is kiwi
  """
  from itertools import tee, islice, chain, izip

  prevs, items, nexts = tee(iterable, 3)
  prevs = chain([None], prevs)
  nexts = chain(islice(nexts, 1, None), [None])
  return izip(prevs, items, nexts)


def get_unique_slug(instance, trigger, max_length=140):
  """
  generate a slug that do not exists in db, incrementing the number. usage sample:

  import miller.helpers

  yom = YourModel()
  print helpers.get_unique_slug(yom, yom.title)

  """
  slug = slugify(trigger)[:max_length]
  slug_exists = True
  counter = 1
  _slug = u'%s' % slug

  while slug_exists:
    try:
      slug_exits = instance.__class__.objects.get(slug=slug)
      if slug_exits:
        slug = _slug + '-' + str(counter)
        counter += 1
    except instance.__class__.DoesNotExist:
      break
  return slug


def create_short_url(): 
  return shortuuid.uuid()[:7]


def get_whoosh_index(force_create=False):
  from whoosh.index import create_in, exists_in, open_dir
  from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
  from whoosh.analysis import CharsetFilter, StemmingAnalyzer
  from whoosh.support.charset import accent_map

  analyzer = StemmingAnalyzer() | CharsetFilter(accent_map)

  schema = Schema(
    title     = TEXT(analyzer=analyzer, stored=True, field_boost=3.0, ), 
    abstract  = TEXT(analyzer=analyzer, stored=True, field_boost=2.0), 
    path      = ID(unique=True, stored=True), 
    authors   = TEXT(analyzer=analyzer, sortable=True, field_boost=1.5), 
    content   = TEXT(analyzer=analyzer, stored=True), 
    tags      = KEYWORD(sortable=True, commas=True, field_boost=1.5, lowercase=True), 
    status    = KEYWORD,
    classname = KEYWORD
  )
    
  if not os.path.exists(settings.WHOOSH_ROOT):
    os.mkdir(settings.WHOOSH_ROOT)
  
  if not exists_in(settings.WHOOSH_ROOT) or force_create:
    index = create_in(settings.WHOOSH_ROOT, schema)
  else:
    index = open_dir(settings.WHOOSH_ROOT)
  return index


def search_whoosh_index(query, *args, **kwargs):
    from whoosh.qparser import MultifieldParser
    from whoosh.query import Term, And, Every
    ix = get_whoosh_index()
    parser = MultifieldParser(['content', 'authors', 'tags', 'title', 'abstract'], ix.schema)
    # user query
    q = parser.parse(query)
    
    if not query:
      q = Every()
      print 'arch'

    allow_q = And([Term(key, value) for key, value in kwargs.iteritems()])
    # parse remaining args
    res = []
    # restrict_q = Or([Term("path", u'%s' % d.id) for d in qs])
    #print 'query', q, allow_q, kwargs
    with ix.searcher() as searcher:
      results = searcher.search(q, filter=allow_q, limit=10, terms=True)
        
      for hit in results:
        res.append({
          'title': hit['title'],
          'short_url': hit['path'],
          'highlights': hit.highlights("content", top=5)
        })
    # @todo filter by empty highlight strings
    return res 


# fill a dictionary with metadata according to the languages specified in settings.py file
def fill_with_metadata(instance, fields=(u'title',u'abstract')):
  metadata = instance.metadata if type(instance.metadata) is dict else json.loads(instance.metadata)
  for field in fields:
    if field not in metadata:
      metadata[field] = {}

    for default_language_code, label, language_code in settings.LANGUAGES:
      if language_code not in metadata[field]:
        metadata[field][language_code] = getattr(instance, field, u'')

  metadata = json.dumps(metadata, indent=1)
  return metadata

# used for metadata multilanguage mapping
def get_languages_dict():
  return dict((language_code,u'') for default_language_code, label, language_code in settings.LANGUAGES)

# Our starting point for zotero related stuffs.
# for a given username, get or create the proper zotero collection.
# Return created<bool>, collection<Collection>, zotero<Zotero>
def get_or_create_zotero_collection(username):
  if not hasattr(settings, 'ZOTERO_IDENTITY'):
    logger.warn('no settings.ZOTERO_IDENTITY found')
    return
  try:
    zot = zotero.Zotero(settings.ZOTERO_IDENTITY, 'user', settings.ZOTERO_API_KEY)
    colls = zot.all_collections()
  except:
    logger.exception('unable to get zotero collections, zotero id: %s, zotero key: %s' % (settings.ZOTERO_IDENTITY, settings.ZOTERO_API_KEY))
    return False, None, None

  # get collection by username (let's trust django username :D)
  for coll in colls:
    if coll['data']['name'] == username:
      return False, coll, zot
  
  # create collection
  collreq = zot.create_collection([{
    'name': username
  }])
  coll = json.loads(collreq)
  if 'successful' in coll:
    # print coll['successful']
    return True, coll['successful']['0'], zot

  logger.warn('unable to create collection, got %s' %collreq)
  return False, None, zot


# filename should be a valid zotero RDF
def fill_zotero_collection(filename, collection, zotero):
  if not zotero:
    logger.warn('no zotero instance found, cfr get_or_create_zotero_collection')
    return
  pass