import os, logging

from django.db.models import Q
from django.conf import settings

from miller.management.commands.task import Command as TaskCommand
from miller.models import Document
from miller import helpers

logger = logging.getLogger('console')

def convert_bytes(num):
  """
  this function will convert bytes to MB.... GB... etc
  """
  for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
      if num < 1024.0:
          return "%3.1f %s" % (num, x)
      num /= 1024.0


class Command(TaskCommand):
  """
  Usage sample:
  python manage.py snapshots all

  """
  help = 'A lot of tasks dealing with snapshots, preview images etc..'


  available_tasks = (
    'optimise',
    'multisize',
    'settings'
  )

  def optimise(self, pk=None, override=False, **options):
    """
    Create an optimised version for documents typed IMAGE attachents.
    Add or update data.resolution.full for the documents, so it needs resolution field to be in place.
    """
    docs = Document.objects.exclude(Q(attachment='') | Q(attachment__exact=None)).filter(type=Document.IMAGE)

    logger.debug('settings.MILLER_ATTACHMENT_MAX_SIZE: {0}'.format(settings.MILLER_ATTACHMENT_MAX_SIZE))
    if pk:
      docs = docs.filter(pk=pk) if pk.isdigit() else docs.filter(slug=pk)

    for doc in docs.iterator():


      if not override and 'resolutions' in doc.data and 'full' in doc.data['resolutions']:
        if pk:
          logger.debug('data field of the selected document already contains "full" resolutions. add --override!')
        continue

      print doc.pk, doc.slug
      print '    type       :', doc.type
      print '    short_url  :', doc.short_url
      print '    orig. path :', doc.attachment.name
      print '    orig. size :', os.stat(doc.attachment.path).st_size, '(', convert_bytes(os.stat(doc.attachment.path).st_size) , ')'


      _, file_extension = os.path.splitext(doc.attachment.name)
      print '    orig. ext  :', file_extension

      filename = Document.snapshot_attachment_file_name(
        instance=doc,
        filename='{pk}.full{ext}'.format(pk=doc.short_url, ext=file_extension)
      )

      print '    new path   :', filename
      newfile = os.path.join(settings.MEDIA_ROOT, filename)

      snapshot = helpers.generate_snapshot(
        filename    = doc.attachment.path,
        output      = newfile,
        width       = None,
        height      = None,
        resolution  = settings.MILLER_ATTACHMENT_RESOLUTION,
        max_size    = settings.MILLER_ATTACHMENT_MAX_SIZE,
        compression_quality    = settings.MILLER_ATTACHMENT_COMPRESSION_QUALITY,
      )

      if not snapshot:
        raise Exception('no snapshot created!')

      print '    new size   :', os.stat(newfile).st_size, '(', convert_bytes(os.stat(newfile).st_size) , ')'

      from PIL import Image, ImageFile

      with Image.open(newfile) as img_file:
        img_file.save(newfile, optimize=True, progressive=True)

      print '    comp. size :', os.stat(newfile).st_size, '(', convert_bytes(os.stat(newfile).st_size) , ')'


      #doc.attachment.name = row['attachment']
      #
      if not 'resolutions' in doc.data:
        doc.data['resolutions'] = {}

      doc.data['resolutions']['full'] = {
        'url': '{host}{file}'.format(host=settings.MILLER_HOST, file=os.path.join(settings.MEDIA_URL, filename)),
        'width': snapshot['thumbnail_width'],
        'height': snapshot['thumbnail_height']
      }

      print '    new width  :', doc.data['resolutions']['full']['width']
      print '    new height :', doc.data['resolutions']['full']['height']

      # doc.attachment.name = filename
      # print doc.data['resolutions']
      doc.save()
      # print newfile # snapshot
      # doc.create_snapshots(custom_logger=logger)
      #doc.save()



  def settings(self, **options):
    logger.debug('settings.MILLER_RESOLUTIONS: {0}'.format(settings.MILLER_RESOLUTIONS))

  def multisize(self, pk=None, override=False, **options):
    self.settings(**options)

    docs = Document.objects.exclude(Q(attachment='') | Q(attachment__exact=None))

    if pk:
      docs = docs.filter(pk=pk)

    print options

    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for doc in docs.iterator():
      if not override and 'resolutions' in doc.data:
        if pk:
          logger.debug('data field of the selected document already contains resolutions. add --override!')
        continue
      doc.create_snapshots(custom_logger=logger)
      doc.save()

      # try:

      #   d = helpers.generate_snapshot(filename=doc.attachment.path, output=outfile, width=settings.MILLER_SNAPSHOT_WIDTH, height=settings.MILLER_SNAPSHOT_HEIGHT)
      # if d:
      #   self.data.update(d)

      #   doc.create_snapshot()
      # except Exception as e:
      #   logger.exception(e)

    logger.info('oh.')
