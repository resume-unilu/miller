"""
ASGI config for miller project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://channels.readthedocs.io/en/stable/deploying.html
and
https://channels.readthedocs.io/en/stable/deploying.html#running-asgi-alongside-wsgi
"""

import os

from channels.asgi import get_channel_layer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "miller.settings")

channel_layer = get_channel_layer()