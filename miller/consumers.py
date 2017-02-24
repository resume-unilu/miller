import json

from actstream.models import Action

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpResponse
from channels import Group
from channels.generic import BaseConsumer
from channels.sessions import channel_session
from channels.auth import http_session_user, channel_session_user, channel_session_user_from_http

from miller.models import Author, Story, Document

@channel_session_user
def ws_receive(message):
  # ASGI WebSocket packet-received and send-packet message types
  # both have a "text" key for their textual data.
  Group("pulse").send({
    "text": message.content['text']
  })
  print 'receive %s' % message.content['text']

  

# Connected to websocket.connect
@channel_session_user_from_http
def ws_connect(message):
  print '%s connected to staff pulse %s' % (message.user.username,message.user.is_staff)
    
  if message.user.is_staff:
    print '%s connected to staff group channel' % (message.user.username,)
    Group("pulse-staff").add(message.reply_channel)
    Group("pulse-staff").send({
      "text": json.dumps({'welcome': 'welcome to the stuff staff channel.'}),
    })

  Group("pulse").add(message.reply_channel)

# Connected to websocket.disconnect
@channel_session_user
def ws_disconnect(message):
  print '%s diconnected to staff pulse %s' % (message.user.username,message.user.is_staff)
    
  if message.user.is_staff:
    Group("pulse-staff").discard(message.reply_channel)
  Group("pulse").discard(message.reply_channel)



# class based view
class PulseConsumer(BaseConsumer):
  method_mapping = {
    "channel.name.here": "method_name",
  }

  def method_name(self, message, **kwargs):
      pass

@receiver(post_save, sender=Action)
def add_action(sender, instance, created, **kwargs):
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




