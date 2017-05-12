import json, requests

from django.core.cache import cache
from django.shortcuts import get_object_or_404

from rest_framework import serializers,viewsets
from rest_framework.decorators import list_route
from rest_framework.exceptions import ValidationError, PermissionDenied, ParseError
from rest_framework.response import Response

from miller.models import Document
from miller.forms import URLForm
from miller.api.serializers import MatchingDocumentSerializer, LiteDocumentSerializer, DocumentSerializer, CreateDocumentSerializer
from miller.api.utils import Glue

from requests.exceptions import HTTPError, Timeout


class DocumentViewSet(viewsets.ModelViewSet):
  queryset = Document.objects.all()
  serializer_class = CreateDocumentSerializer
  list_serializer_class = LiteDocumentSerializer

  # retrieve by PK or slug
  def retrieve(self, request, *args, **kwargs):

    if 'pk' in kwargs and not kwargs['pk'].isdigit():
      doc = get_object_or_404(Document, slug=kwargs['pk'])  
      # save, then return tagged items according to tagform
      serializer = DocumentSerializer(doc,
          context={'request': request},
      )
      return Response(serializer.data)
    self.serializer_class = DocumentSerializer
    return super(DocumentViewSet, self).retrieve(request, *args, **kwargs)
    

  def list(self, request):
    g = Glue(request=request, queryset=self.queryset.distinct())
    page    = self.paginate_queryset(g.queryset)
    serializer = self.list_serializer_class(page, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)



  @list_route(methods=['get'])
  def search(self, request):
    from miller.forms import SearchQueryForm
    from miller.helpers import search_whoosh_index
    form = SearchQueryForm(request.query_params)
    if not form.is_valid():
      return Response(form.errors, status=status.HTTP_201_CREATED)
    # get the results
    results = search_whoosh_index(form.cleaned_data['q'], classname=u'document')
    
    filters = {
      'short_url__in': [hit['short_url'] for hit in results]
    }
    # check if the user is allowed this content
    docs = self.queryset.filter(**filters)
    
    def mapper(d):
      d.matches = []
      for hit in results:
        if d.short_url == hit['short_url']:
          d.matches = hit
          break
      return d
    # enrich docs items (max 10 items)
    docs = map(mapper, docs)
    page    = self.paginate_queryset(docs)

    serializer = MatchingDocumentSerializer(docs, many=True,
      context={'request': request}
    )
    return self.get_paginated_response(serializer.data)


  @list_route(methods=['get'])
  def oembed(self, request):
    if not request.user.is_authenticated:
      raise PermissionDenied()

    """
    check if a document url exists in our system;
    if not, load 
    # do a request to intercept 404 requests. Otherwise: go to iframely; or embed.ly
    """
    form = URLForm(request.GET)
    if not form.is_valid():
      raise ValidationError(form.errors)  

    # check if there is no document
    url = form.cleaned_data['url']

    ckey = 'oembed:%s' % url

    if cache.has_key(ckey):
      return Response(cache.get(ckey))

    def perform_request(url, headers={}, params=None, timeout=5):
      try:
        res = requests.get(url, headers=headers, params=params, timeout=timeout)
      except Exception as e:
        raise ParseError({
          'error': '%s' % e
        })

      try:
        res.raise_for_status()
      except HTTPError as e:
        raise ParseError({
          'error': '%s' % e
        })
      
      return res

    res = perform_request(url, headers={'Range':'bytes=0-20000'})

    if res.headers.get('content-type') in ("application/pdf", "application/x-pdf",):
      provider_url = self.headers.get('Host', None)
      if not provider_url:
        from urlparse import urlparse
        o = urlparse(url)
        provider_url = o.netloc

      return Response({
        "url": url,
        "provider_url": provider_url, 
        "title": "", 
        "height": 780, 
        "width": 600, 
        "html": "<iframe src=\"https://drive.google.com/viewerng/viewer?url=%s&embedded=true\" width=\"600\" height=\"780\" style=\"border: none;\"></iframe>" % url, 
        "version": "1.0", 
        "provider_name": res.headers.get('server', ''), 
        "type": "rich",
        "info": {
          'service': 'miller',
        }
      })


    # check noembed! e.g; for flickr. We should check if the url is in the pattern specified.
    noembed = perform_request('https://noembed.com/embed', params={
      'url': url
    });
    d = noembed.json()

    if not 'error' in d:
      d.update({
        "info": {
          'service': 'noembed'
        }
      })
      return Response(d)

    import opengraph
    og = opengraph.OpenGraph(html=res.text)
    ogd = dict(og.items())
    print ogd
    d = {
      "url": url,
      "encoding": res.encoding,
      "provider_name":  ogd.get('site_name'),
      "title": ogd.get('title'),
      "description": ogd.get('description'),
      "type": "link",
    }

    if ogd.get('image'): 
      d.update({
        "thumbnail_url" : ogd.get('image'),
        "thumbnail_width" : ogd.get('image:width'),
        "thumbnail_height" : ogd.get('image:height'),
      })


    # custom from og
    return Response(d)

   

    # check embedly!




