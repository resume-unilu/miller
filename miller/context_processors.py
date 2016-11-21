import json
from django.conf import settings

# inject some miller specific settings used by angular
def default(request):
  context_settings = {
    'title': settings.MILLER_TITLE,
    'debug': settings.MILLER_DEBUG,
    'settings': json.dumps(settings.MILLER_SETTINGS),
    'oembeds': json.dumps(settings.MILLER_OEMBEDS),
    
  }
  return context_settings