import json, logging

from django.apps import apps
from django.http import HttpResponse
from channels import Group
from channels.generic import BaseConsumer
from channels.sessions import channel_session
from channels.auth import http_session_user, channel_session_user, channel_session_user_from_http

from miller.models import Author, Story, Document


logger = logging.getLogger('miller')


def broadcast(group, message):
  """
  send a message dict
  """
  #logger.debug('BROADCASTING to channel %s, msg %s' % (group,message))
  message.update({'_broadcast_group': group})
  Group(group).send({
    "text": json.dumps(message),
  })


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
  logger.debug('%s connected to staff pulse %s' % (message.user.username,message.user.is_staff))
    
  if message.user.is_staff:
    print '%s connected to staff group channel' % (message.user.username,)
    Group("pulse-staff").add(message.reply_channel)
    broadcast("pulse-staff", {'welcome': 'welcome to the stuff staff channel.'})

  # send per user channel:
  
  if message.user.is_authenticated:
    Group("pulse-%s" % message.user.username ).add(message.reply_channel)
    broadcast("pulse-%s" % message.user.username, {
      'welcome': 'welcome to your own channel, %s. Here you\'ll be notified for comments on your stories.' % message.user.username
    })

  Group("pulse").add(message.reply_channel)
  broadcast("pulse", {'welcome': 'welcome to the lite notification channel. Public notifications are here.'})

# Connected to websocket.disconnect
@channel_session_user
def ws_disconnect(message):
  logger.debug('%s DISCONNECTED to staff pulse %s' % (message.user.username,message.user.is_staff))
    
  if message.user.is_staff:
    Group("pulse-staff").discard(message.reply_channel)
  if message.user.is_authenticated:
    Group("pulse-%s" % message.user.username).discard(message.reply_channel)
  Group("pulse").discard(message.reply_channel)



# class based view
class PulseConsumer(BaseConsumer):
  method_mapping = {
    "channel.name.here": "method_name",
  }

  def method_name(self, message, **kwargs):
      pass


