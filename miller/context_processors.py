import json, os
from django.conf import settings
from django.utils import translation
from miller.api.serializers import HeavyProfileSerializer

# inject some miller specific settings used by angular
def default(request):
  profile = HeavyProfileSerializer(request.user.profile).data if hasattr(request.user, 'profile') else {
    'authors': [],
    'groups': []
  }

  # pages = [fname.replace('.md', '') for fname in os.listdir(settings.PAGES_ROOT) if fname.endswith('.md')]
  pages = settings.MILLER_STATIC_PAGES

  context_settings = {
    'title': settings.MILLER_TITLE,
    'debug': settings.MILLER_DEBUG,
    'host': settings.MILLER_SETTINGS['host'], # get_host() fails behind proxy. we do it manually in settings.
    'settings': json.dumps(settings.MILLER_SETTINGS),
    'oembeds': json.dumps(settings.MILLER_OEMBEDS),
    'profile': json.dumps( profile ),
    'language': translation.get_language(),
    'pages': pages
  }
  return context_settings