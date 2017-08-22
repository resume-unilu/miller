# a collection of embedding functions
import requests, re
from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework.exceptions import ValidationError, PermissionDenied, ParseError, NotFound
from requests.exceptions import HTTPError

def perform_request(url, headers={}, params=None, timeout=5):
  """
  perform request. Raise errors.
  """
  try:
    res = requests.get(url, headers=headers, params=params, timeout=timeout)
  except Exception as e:
    raise ParseError({
      'error': '%s' % e
    })

  try:
    res.raise_for_status()
  except HTTPError as e:
    if e.response.status_code == 404:
      raise NotFound({
        'error': '%s' % e
      })

    raise ParseError({
      'error': '%s' % e
    })

  return res


def timelinejs(m):
  """
  add support for knightlab timelines (as rich links)
  Follow the https://timeline.knightlab.com/docs/instantiate-a-timeline.html

  e.g. http://cdn.knightlab.com/libs/timeline3/latest/embed/index.html?source=0AmNxBKGzRxw8dE9rbThJX0RCUmxheW1oOUMxWEdLd3c&font=Georgia-Helvetica&maptype=TERRAIN&lang=en&height=650
  """
  url = 'https://%s' % m.group('path')
  # get the google spreadsheet id
  gsid = re.search(r'source=(.*)', url)
  if not gsid:
    return None

  gsid = gsid.group(1)

  d = {
    "url": url,
    "html": '<iframe src="%(host)s/timelinejs/%(gsid)s" frameBorder="0"></iframe>' % {
      'host': settings.MILLER_HOST,
      'gsid': gsid
    },
    "type": "timeline",
    "version": "1.0",
    "provider_name": 'TimelineJS',
  }
  return d


def custom_noembed(url, content_type, provider_url):
  d = None
  if content_type in ("application/pdf", "application/x-pdf",):
    d = {
      "url": url,
      "title": "",
      "height": 780,
      "width": 600,
      "html": "<iframe src=\"https://drive.google.com/viewerng/viewer?url=%s&embedded=true\" width=\"600\" height=\"780\" style=\"border: none;\"></iframe>" % url,
      "version": "1.0",
      "provider_name": provider_url,
      "type": "rich",
    }
  elif content_type.startswith('image/'):
    d = {
      "url": url,
      "title": "",
      "height": 780,
      "width": 600,
      "version": "1.0",
      "provider_name": provider_url,
      "type": "photo",
      "info": {
        'service': 'miller',
      }
    }

  if not d:
    # test agianst custom url patterns
    for _type, _pattern, _fn in settings.MILLER_OEMBEDS_MAPPER:
      match = re.search(_pattern, url)
      if match:
        d = import_string(_fn)(match)
        break;

  if d is not None:
    d.update({
      "provider_url": provider_url,
      "info": {
        'service': 'miller',
      }
    })
  return d