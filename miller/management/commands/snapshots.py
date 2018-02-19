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
