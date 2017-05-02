import os, re, mimetypes

from django.conf import settings


from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response

from wand.image import Image

from miller.helpers import streamHttpResponse






@api_view()
def images(request):
  if not request.user.is_authenticated:
    raise NotAuthenticated()
  #_c[10,20,50,100]
  # before the last point.
  if not 'url' in request.GET:
    return Response({"error": "missing url param"},  status=status.HTTP_422_UNPROCESSABLE_ENTITY)

  # search for something like ?url=/media/image/2162934893_b053386d3f_o_c[100,20,500,200].jpg
  # where the original image is this part: /media/image/2162934893_b053386d3f_o.jpg
  ms = re.search(r'\/media\/(?P<path>[_\/a-z\d\-]+)_(?P<funcs>[a-z\[\],\d]+)\.(?P<ext>jpg|gif|jpeg)$', request.GET['url'])

  if ms is None:
    return Response({"error": "invalid url param"},  status=status.HTTP_422_UNPROCESSABLE_ENTITY)

  # get the groups from our regex
  basepath  = os.path.normpath(ms.group('path'))
  ext       = ms.group('ext')
  functions = ms.group('funcs')

  # input filename (original) and output filename (modified)
  filename    = os.path.join(settings.MEDIA_ROOT, '%s.%s'% (basepath,ext))
  filenameout = os.path.join(settings.MEDIA_ROOT, '%s_%s.%s'% (basepath,functions,ext))
  
  if not os.path.exists(filename):
    return Response({"error": "requested image was not found"}, status=status.HTTP_404_NOT_FOUND)

  if os.path.exists(filenameout):
    return streamHttpResponse(filenameout)

  # get distinct wand methods
  funcs = re.findall(r'(?P<func>[a-z])\[(?P<args>[\d,]+)\]',functions)
  
  available_funcs = {
    'c': 'crop'
  }

  with Image(filename=filename) as img:
    for a,b in funcs:
      try:
        getattr(img,available_funcs[a])(*map(int,b.split(',')))
        img.save(filename=filenameout)
      except KeyError as e:
        return Response({"exception": '%s' % e, 'type': 'KeyError'},  status=status.HTTP_400_BAD_REQUEST)
      except ValueError as e:
        return Response({"exception": '%s' % e, 'type': 'ValueError'},  status=status.HTTP_400_BAD_REQUEST)
      else:
        return streamHttpResponse(filenameout)