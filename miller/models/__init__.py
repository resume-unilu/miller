# __init__.py
import logging, json

from profile import Profile
from tag import Tag
from document import Document
from author import Author
from story import Story
from caption import Caption
from mention import Mention
from comment import Comment
from review import Review
from page import Page

from miller.consumers import broadcast
from django.db.models.signals import post_save
from django.dispatch import receiver
from actstream.models import Action

logger = logging.getLogger('miller')


@receiver(post_save, sender=Action)
def add_action(sender, instance, created, **kwargs):
  try:
    from miller.api.utils import get_serialized

    data = {
      'actor': get_serialized(instance.actor),
      'actor_type': instance.actor_content_type.model,

      'verb': instance.verb,
      
      'target': get_serialized(instance.target),
      'target_content_type': instance.target_content_type.model,

      'timesince': instance.timesince(),

      'info': instance.data
    }

    if data['target_content_type'] == 'story':
      for u in instance.target.authors.values('user__username'):
        broadcast("pulse-%s"% u['user__username'], data)
      for u in instance.target.reviews.values_list('assignee__username', flat=True):
        broadcast("pulse-%s"% u, data)
    broadcast('pulse-staff', data)

  except Exception as e:
    logger.exception(e)
  else:
    logger.debug('action sent to channel pulse-staff')
  