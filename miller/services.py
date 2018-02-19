import os, re, mimetypes

from django.conf import settings


from rest_framework import status
from rest_framework.authentication import SessionAuthentication,TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response

from wand.image import Image
from wand.exceptions import ModuleError

from miller.helpers import streamHttpResponse, generate_snapshot


class TokenAuthSupportQueryString(TokenAuthentication):
  def authenticate(self, request):
    if 'token' in request.query_params:
      return self.authenticate_credentials(request.query_params.get('token').strip())
    else:
      return super(TokenAuthSupportQueryString, self).authenticate(request)

@api_view()
def suggest(request):
  if not request.user.is_authenticated:
    raise NotAuthenticated()

  if not 'q' in request.GET:
    return Response({"error": "missing url param"},  status=status.HTTP_422_UNPROCESSABLE_ENTITY)

  # q = request.GET.
  

@api_view()
#@authentication_classes([SessionAuthentication, TokenAuthSupportQueryString])
def images(request):
  """
  request sample
  for thumbnail: 
  ?url=<filebasename>_T[width,height].<extension>
  for cropping (http://docs.wand-py.org/en/0.4.1/wand/image.html)
  ?url=<filebasename>_c[300,300,310,310].<extension>
  or
  ?url=<filebasename>_c[300,300].<extension>
  """
  #if not request.user.is_authenticated:
  #  raise NotAuthenticated()
  #_c[10,20,50,100]
  # before the last point.
  if not 'url' in request.GET:
    return Response({"error": "missing url param"},  status=status.HTTP_422_UNPROCESSABLE_ENTITY)

  # search for something like ?url=/media/image/2162934893_b053386d3f_o_c[100,20,500,200].jpg
  # where the original image is this part: /media/image/2162934893_b053386d3f_o.jpg
  ms = re.search(r'\/media\/(?P<path>[a-zA-Z_\/\d\-]+)_(?P<funcs>[a-zA-Z\[\]\-\d\!\^%,]+)\.(?P<ext>jpg|gif|jpeg|jpe)$', request.GET['url'])

  if ms is None:
    return Response({"error": "invalid url param", "url": request.GET['url']},  status=status.HTTP_422_UNPROCESSABLE_ENTITY)

  # get the groups from our regex
  basepath  = os.path.normpath(ms.group('path'))
  ext       = ms.group('ext')
  functions = ms.group('funcs')

  # input filename (original) and output filename (modified)
  filename    = os.path.join(settings.MEDIA_ROOT, '%s.%s'% (basepath,ext))
  filenameout = os.path.join(settings.MEDIA_ROOT, '%s_%s.%s'% (basepath,functions,ext))
  
  if not os.path.exists(filename):
    return Response({"error": "requested image was not found"}, status=status.HTTP_404_NOT_FOUND)

  #if os.path.exists(filenameout):
  #  return streamHttpResponse(filenameout)

  # get distinct wand methods
  funcs = re.findall(r'(?P<func>[a-zA-Z])\[?(?P<args>[\d\-%x,]+)\]?',functions)

  if not funcs:
    return Response({"error": "invalid url param - url does not contain any valid resize function.", "url": request.GET['url']},  status=status.HTTP_422_UNPROCESSABLE_ENTITY)

  available_funcs = {
    'c': 'crop',
    't': 'transform', # crop and resize
    'T': 'thumbnail',
    'r': 'resize',
    'F': 'fit'
  }

  with Image(filename=filename, resolution=300) as img:
    for a,b in funcs:
      if a == 'T':
        args = map(lambda x: int(x) if x.isnumeric() else x,b.split(','))
        generate_snapshot(filename, filenameout, width=args[0], height=args[-1], crop=True)
        return streamHttpResponse(filenameout)
      else:
        args = map(lambda x: int(x) if x.isnumeric() else x, b.split(','))
      if a == 'F':
        generate_snapshot(filename, filenameout, width=args[0])
        return streamHttpResponse(filenameout)
      try:
        getattr(img,available_funcs[a])(*args)
        img.resolution = (settings.MILLER_CROPPING_RESOLUTION, settings.MILLER_CROPPING_RESOLUTION)
        # transform resize image automatically based on settings
        if settings.MILLER_CROPPING_AUTO_RESIZE:
          # calculate ratio 
          ratio = 1.0*img.width/img.height
          # dummy var init
          width = height = 0
          if img.width > img.height:
            width = settings.MILLER_CROPPING_MAX_SIZE
            height = width / ratio
          elif img.width < img.height:
            height = max_size
            width = ratio * height
          else: 
            #squared image
            height = width = max_size
          img.transform(resize='%sx%s'% (width, height))
        img.save(filename=filenameout)
      except TypeError as e:
        return Response({"exception": '%s' % e, 'type': 'TypeError'},  status=status.HTTP_400_BAD_REQUEST)
      except KeyError as e:
        return Response({"exception": '%s' % e, 'type': 'KeyError'},  status=status.HTTP_400_BAD_REQUEST)
      except ValueError as e:
        return Response({"exception": '%s' % e, 'type': 'ValueError'},  status=status.HTTP_400_BAD_REQUEST)
      except ModuleError as e:
        print e
        return Response({"exception": '%s' % e, 'type': 'ModuleError'},  status=status.HTTP_400_BAD_REQUEST)
      except NameError as e:
        return Response({"exception": '%s' % e, 'type': 'NameError'}, status=status.HTTP_400_BAD_REQUEST)
      else:
        return streamHttpResponse(filenameout)