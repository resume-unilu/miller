from django.http import HttpResponse
from channels import Group
from channels.generic import BaseConsumer
from channels.sessions import channel_session
from channels.auth import http_session_user, channel_session_user, channel_session_user_from_http

@channel_session_user
def ws_receive(message):
  # ASGI WebSocket packet-received and send-packet message types
  # both have a "text" key for their textual data.
  Group("pulse").send({
    "text": message.content['text'],
  })
  print 'receive %s' % message.content['text']
  
  Group("pulse-staff").send({
    "text": 'welcome to the stuff staff channel',
  })

# Connected to websocket.connect
@channel_session_user_from_http
def ws_connect(message):
  print '%s connected to staff pulse %s' % (message.user.username,message.user.is_staff)
    
  if message.user.is_staff:
    print '%s connected to staff group channel' % (message.user.username,)
    Group("pulse-staff").add(message.reply_channel)
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