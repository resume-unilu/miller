from channels.routing import route
from miller.consumers import ws_connect, ws_receive, ws_disconnect

channel_routing = [
    route("websocket.connect", ws_connect),
    route("websocket.receive", ws_receive),
    route("websocket.disconnect", ws_disconnect),
]