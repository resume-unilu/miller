# __init__.py
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



import logging, json

from channels import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from actstream.models import Action

logger = logging.getLogger('miller')

@receiver(post_save, sender=Action)
def add_action(sender, instance, created, **kwargs):
  try:
    from miller.api.utils import get_serialized

    # pseudo serializer ;)
    msg = json.dumps({
      'actor': get_serialized(instance.actor),
      'verb': instance.verb,
      'action_object': instance.actor_content_type.model,
      'target': get_serialized(instance.target),
      'timesince': instance.timesince()
    })
    Group("pulse-staff").send({
      "text": msg,
    })
  except Exception as e:
    logger.exception(e)
  else:
    logger.debug('action sent to channel pulse-staff')
  