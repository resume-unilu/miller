from django.http import HttpResponse
from channels import Group


def ws_message(message):
  # ASGI WebSocket packet-received and send-packet message types
  # both have a "text" key for their textual data.
  message.reply_channel.send({
      "text": message.content['text'],
  })

# Connected to websocket.connect
def ws_add(message):
  Group("chat").add(message.reply_channel)

# Connected to websocket.disconnect
def ws_disconnect(message):
  Group("chat").discard(message.reply_channel)