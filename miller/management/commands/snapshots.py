import os, logging

from django.db.models import Q
from django.conf import settings

from miller.management.commands.task import Command as TaskCommand
from miller.models import Document
from miller import helpers

logger = logging.getLogger('console')


class Command(TaskCommand):
  """
  Usage sample: 
  python manage.py snapshots all

  """
  help = 'A lot of tasks dealing with snapshots, preview images etc..'
  

  available_tasks = (
    'all',
    'multisize',
    'settings'
  )

  def all(self, pk=None, **options):
    pass

  def settings(self, **options):
    logger.debug('settings.MILLER_RESOLUTIONS: {0}'.format(settings.MILLER_RESOLUTIONS))

  def multisize(self, pk=None, **options):
    self.settings(**options)

    docs = Document.objects.exclude(Q(attachment='') | Q(attachment__exact=None))

    if pk:
      docs = docs.filter(pk=pk)

    print options

    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for doc in docs.iterator():
      
      if not doc.attachment or not getattr(doc.attachment, 'path', None):
        logger.warning('  pk={0} snapshot cannot be generated.'.format(doc.pk))
        continue

      if not os.path.exists(doc.attachment.path):
        logger.warning('  pk={0} snapshot cannot be generated, attached file does not exist.'.format(doc.pk))
        continue

      
      if doc.mimetype.split('/')[0] == 'image' or doc.type in [Document.IMAGE, Document.PHOTO]:
        logger.debug('  pk={0} snapshot type={1}'.format(doc.pk, doc.type))
        
        _d = {}

        for field, resolution, max_size in settings.MILLER_RESOLUTIONS:

          print field
          filename = Document.snapshot_attachment_file_name(doc, filename='{pk}.{field}.jpg'.format(pk=doc.short_url, field=field))
          outfile = os.path.join(settings.MEDIA_ROOT, filename)

          print outfile, doc.attachment.path
          _d[field] = {
            'url': filename
          }
          size = helpers.generate_snapshot(filename=doc.attachment.path, output=outfile, width=max_size, height=None, resolution=resolution)
          print size
        doc.data['resolutions'] = _d
        
          #Document.snapshot_attachment_file_name(doc, )

        print doc.data

      # try:
        
      #   d = helpers.generate_snapshot(filename=doc.attachment.path, output=outfile, width=settings.MILLER_SNAPSHOT_WIDTH, height=settings.MILLER_SNAPSHOT_HEIGHT)
      # if d:
      #   self.data.update(d)

      #   doc.create_snapshot()
      # except Exception as e:
      #   logger.exception(e)

    logger.info('oh.')
