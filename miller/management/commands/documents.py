#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tasks for documents
import logging, json, re, os, collections
from .task import Command as TaskCommand
from .utils import get_data_from_dict, get_dirlist
from miller.models import Profile, Document
from django.conf import settings
from pydash import flatten

logger = logging.getLogger('console')


class Command(TaskCommand):
  available_tasks = (
    'import_from_json',
    'set_related_docs_from_json',
    'reset',
  )

  def add_arguments(self, parser):
    super(Command, self).add_arguments(parser)
    parser.add_argument(
      '--file',
      dest = 'filepath',
      default = None,
      help = 'google spreadsheet file',
    )
    parser.add_argument(
      '--strict',
      dest = 'strict',
      default = False,
      help = 'apply stricter rules',
    )

  def set_related_docs_from_json(self, filepath, strict, **options):
    """
    Update the document table with the documents stored in the json file
    specified in param `filepath`.
    For each item, two properties are compulsory:
    - "slug"
    - "related_documents|list"
    The JSON file comes thanks to the [google-spreadsheet-to-json](https://www.npmjs.com/package/google-spreadsheet-to-json)

    usage:
    python manage.py documents set_related_docs_from_json --file ./docs.json
    """
    if filepath is None:
      raise Exception('filepath should be specified')
    logger.debug('set_related_docs_from_json {0}'.format(filepath))
    with open(filepath) as f:
      docs = filter(lambda x: 'slug' in x and 'related_documents|list' in x, flatten(json.load(f)))

    if not docs:
      raise Exception('json file looks empty (or no fields with \'slug\' in x and \'related_documents|list\' in x)!')
    logger.debug('found {0} docs'.format(len(docs)))

    for i, row in enumerate(docs):
      related_documents = filter(None, row.get('related_documents|list', '').split(','))
      slug = row.get('slug').strip()
      logger.debug('document "{0}" need to be connected to: {1}'.format(slug, related_documents))
      try:
        doc = Document.objects.get(slug=slug)
      except Document.DoesNotExist:
        logger.error('document {0} does not exist'.format(slug))
      else:
        related = Document.objects.filter(slug__in=related_documents)
        # since this is a symmetrical relationship, we do the cleansing before bulk importing the data.
        # This should happens in a separate command.
        # doc.documents.clear()
      doc.documents.add(*related)
      doc.save()
      logger.debug('document "{0}" connected to: "{1}"'.format(slug,[d.slug for d in doc.documents.all()]))



  def import_from_json(self, filepath, strict, pk, **options):
    """
    Update the document table with the documents stored in the json file
    specified in param `filepath`.
    The JSON file comes thanks to the [google-spreadsheet-to-json](https://www.npmjs.com/package/google-spreadsheet-to-json)

    usage:

        python manage.py documents import_from_json --file ./docs.json

    or, for single document

        python manage.py documents import_from_json --file ./docs.json --pk doc-slug

    If there is a not-empty `attachment` property, the `strict` option
    checks whether the given path actually exists; otherwise it blocks the import task.
    """
    if filepath is None:
      raise Exception('filepath should be specified')
    logger.debug('import_from_json {0}'.format(filepath))

    owner = Profile.objects.filter(user__is_staff=True).first()
    logger.debug('owner (only for new docs) {0}'.format(owner.user.username))

    with open(filepath) as f:
      docs = filter(lambda x: 'slug' in x, flatten(json.load(f)))
      if pk is not None:
        logger.debug('--pk param specified, we update documents where pk={0} ...'.format(pk))
        docs = filter(lambda x: x['slug'] == pk, docs)

      # check duplicates in slug field.
      slugs = map(lambda x: x['slug'], docs)
      unique_slugs = set(slugs)
      if len(slugs) != len(unique_slugs):
        dupes = [item for item, count in collections.Counter(slugs).items() if count > 1]
        raise Exception('there are {0} duplicates: {1}'.format(len(dupes), dupes))

    if not docs:
      raise Exception('json file looks empty!')

    logger.debug('found {0} docs'.format(len(docs)))
    logger.debug('headers: {0} '.format(docs[0].keys()))
    logger.debug('update fields: {0}'.format(settings.MILLER_IMPORT_DOCUMENTS_FIELDS))

    for i, row in enumerate(docs):
      if not row['slug'] or not row['type']:
        # logger.debug('line %s: empty "slug" or empty "type", skipping.' % i)
        continue

      slug = re.sub('\s','',row['slug'])
      type = row['type'].strip()
      has_attachment = 'attachment' in row and row['attachment'] and len(row['attachment'].strip()) > 0
      has_snapshot = 'snapshot' in row and row['snapshot'] and len(row['snapshot'].strip()) > 0

      # print(i, slug, type);

      try:
        doc = Document.objects.get(slug=slug)
      except Document.DoesNotExist:
        doc = Document(slug=slug, type=type, owner=owner.user)


      # update non data fields
      for key in settings.MILLER_IMPORT_DOCUMENTS_FIELDS:
        try:
          setattr(doc, key, row[key])
        except KeyError:
          pass

      # udpate data fields (basically, fill empty data_structure)
      doc_data = get_data_from_dict(row)
      doc.data.update(doc_data['data'])

      if has_attachment:
        # must be relative to MEDIA_ROOT
        attachment_path    = row['attachment'].strip()
        attachment_abspath = os.path.join(settings.MEDIA_ROOT, attachment_path)
        attachment_exists  = os.path.exists(attachment_abspath)

        if strict and re.match(r'^[a-zA-Z\-\d_/\.àéèçàâôûîê]+$', attachment_path) is None:
          logger.error(u'item {0}: attachment "{1}" does not match slug rules, exit'.format(slug, attachment_path))
          break
        # logger.debug(u'line {0}: attachment found, \n   - datum: {1}\n   - real: {2}\n   exists: {3}'.format(i, row['attachment'], _attachment_abspath, _attachment_exists))
        # check that the file exists; otherwise skip everything
        if strict and not attachment_exists:
          logger.warning(u'line {0}: no real path has been found for the attachment, skipping. Path: {1}'.format(i, attachment_path))
          break
        logger.info(u'item "{0}"({1}) has attachment "{2}"'.format(slug, type, attachment_path))

        doc.attachment.name = attachment_path

      # check if the type/slug correspond to a real dir below MEDIA_ROOT
      dirpath = os.path.join(settings.MEDIA_ROOT, u'{type}/{slug}'.format(
        type=type,
        slug=slug
      ))

      if os.path.isdir(dirpath):
        logger.info('Document {0} has a matching media folder, dirpath: {1}'.format(slug, dirpath))

        # in this case, attachment is a folder containing all items
        doc.data.update({
          'sources': get_dirlist(
            dirpath = dirpath,
            media_url = '{type}/{slug}'.format(
              type = type,
              slug = slug
            ),
            types = settings.MILLER_3DOBJECT_TYPES + settings.MILLER_AUDIO_SOURCES_TYPES
          )
        })


      if type == 'video':
        # look for language specific subtitles in the video folder.
        subtitles = {}
        for extension, submimetype in settings.MILLER_VIDEO_SUBTITLES_TYPES:
          subtitles[extension] = {}

          for c,t,lang,s in settings.LANGUAGES:
            # verify that the file exist.
            subtitle_filename = 'video/{slug}.{lang}.{extension}'.format(**{
              'slug': slug,
              'lang': lang,
              'extension': extension
            })
            subtitle_filepath = os.path.join(settings.MEDIA_ROOT, subtitle_filename)

            if os.path.exists(subtitle_filepath):
              logger.info(u'item "{0}"({1}) local {2} subtitles FOUND for {3} at {4}'.format(
                slug, type, extension, lang, subtitle_filepath
              ))
              subtitles[extension][lang] = os.path.join(settings.MILLER_HOST, '/'.join(s.strip('/') for s in [settings.MEDIA_URL, subtitle_filename]))
            else:
              logger.warning(u'item "{0}"({1}) local {2} subtitles for {3} NOT FOUND at {4}'.format(
                slug, type, extension, lang, subtitle_filepath
              ))

        doc.data.update({
          'subtitles': subtitles
        })

      doc.save()
      logger.info(u'item "{0}"({1}) completed.\n'.format(slug, type))
