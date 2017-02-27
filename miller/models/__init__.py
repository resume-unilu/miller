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

    data = {
      'actor': get_serialized(instance.actor),
      'actor_type': instance.actor_content_type.model,

      'verb': instance.verb,
      
      'target': get_serialized(instance.target),
      'target_type': instance.target_content_type.model,

      'timesince': instance.timesince()
    }

    msg = json.dumps(data)

    if data['target_type'] == 'story':
      for u in instance.target.authors.values('user__username'):
        Group("pulse-" + u['user__username']).send({
          "text": msg,
        })

    Group("pulse-staff").send({
      "text": msg,
    })

  except Exception as e:
    logger.exception(e)
  else:
    logger.debug('action sent to channel pulse-staff')
  