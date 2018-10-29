#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tasks for documents
import logging, json, re, os
from .task import Command as TaskCommand
from .utils import get_data_from_dict
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



  def import_from_json(self, filepath, strict, **options):
    """
    Update the document table with the documents stored in the json file
    specified in param `filepath`.
    The JSON file comes thanks to the [google-spreadsheet-to-json](https://www.npmjs.com/package/google-spreadsheet-to-json)

    usage:

    """
    if filepath is None:
      raise Exception('filepath should be specified')
    logger.debug('import_from_json {0}'.format(filepath))

    owner = Profile.objects.filter(user__is_staff=True).first()
    logger.debug('owner (only for new docs) {0}'.format(owner.user.username))

    with open(filepath) as f:
      docs = filter(lambda x: 'slug' in x, flatten(json.load(f)))

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

        if type == 'audio':
          # logger.info('line {line}: adding audio'.format(line=i))
          sources = []
          for extension, audiomimetype in settings.MILLER_AUDIO_SOURCES_TYPES:
            # verify that the file exist.
            audiosource = '{filename}.{extension}'.format(
              filename=os.path.basename(os.path.splitext(attachment_path)[0]),
              extension=extension
            )
            audiosource_abspath = os.path.join(os.path.dirname(attachment_abspath), audiosource)
            if os.path.exists(audiosource_abspath):
              logger.debug('line {line}: adding audio {extension}, source={source}'.format(line=i, extension=extension, source=audiosource_abspath))
              sources.append({
                'src': '{host}{file}'.format(
                    host=settings.MILLER_HOST,
                    file=os.path.join(
                        settings.MEDIA_URL,
                        os.path.dirname(attachment_path), audiosource
                )),
                'type': audiomimetype
              })
            else:
              logger.warning('line {line}: CANNOT ADD audio {extension}, source={source} not found'.format(line=i, extension=extension, source=audiosource_abspath))

          # print extension, audiosource
          doc.data.update({
            'sources': sources
          })


      doc.save()
      logger.info(u'item "{0}"({1}) completed.\n'.format(slug, type))

    
