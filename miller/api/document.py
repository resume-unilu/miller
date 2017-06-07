import json, requests

from django.core.cache import cache
from django.shortcuts import get_object_or_404

from rest_framework import serializers,viewsets
from rest_framework.decorators import list_route
from rest_framework.exceptions import ValidationError, PermissionDenied, ParseError, NotFound
from rest_framework.response import Response

from miller.models import Document
from miller.forms import URLForm, SearchQueryForm
from miller.api.serializers import MatchingDocumentSerializer, LiteDocumentSerializer, DocumentSerializer, CreateDocumentSerializer
from miller.api.utils import Glue

from requests.exceptions import HTTPError, Timeout
from .pagination import FacetedPagination


class DocumentViewSet(viewsets.ModelViewSet):
  queryset = Document.objects.all()
  serializer_class = CreateDocumentSerializer
  list_serializer_class = LiteDocumentSerializer
  pagination_class = FacetedPagination

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
    """
    Deprecated in favor of using simpler q in http request
    /api/document/?q=world
    cfr. utils.Glue class
    """
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
    g = Glue(request=request, queryset=self.queryset.filter(**filters).distinct())
    docs = g.queryset

    def mapper(d):
      d.matches = []
      for hit in results:
        if d.short_url == hit['short_url']:
          d.matches = hit
          break
      return d
    # enrich docs items (max 10 items)
    #docs = map(mapper, docs)
    page = self.paginate_queryset(docs)

    serializer = MatchingDocumentSerializer(map(mapper,page), many=True,
      context={'request': request}
    )
    return self.get_paginated_response(serializer.data)


  @list_route(methods=['get'])
  def suggest(self, request):
    """
    quggest querystring based on this model search 
    """
    form = SearchQueryForm(request.query_params)
    if not form.is_valid():
      return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
    
    from django.contrib.postgres.search import SearchVector

    # queryset = self.queryset.annotate(
    #   sv=SearchVector('data__title'),
    # ).filter(sv=form.cleaned_data['q'])
    queryset = self.queryset.filter(Q(title__icontains=form.cleaned_data['q']) | Q(data__title__en_US__icontains=form.cleaned_data['q']))

    return Response({
      'results': queryset.values_list('title', flat=True)
    })



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

    if not request.query_params.get('nocache', None) and cache.has_key(ckey):
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
        if e.response.status_code == 404:
          raise NotFound({
            'error': '%s' % e
          })

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

      d = {
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
      }

      cache.set(ckey, d)
      return Response(d)


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

    d = {
      "url": url,
      "encoding": res.encoding,
      #"provider_name":  ogd.get('site_name'),
      #"description": ogd.get('description'),
      "type": "link",
      "html": ''
    }

    def quickmeta(doc, name, attrs={}):
      attrs.update({
        'name': name
      })

      m = doc.html.head.findAll('meta', attrs=attrs)

      return None if not m else u"".join([t['content'] for t in m])



    # get opengraph data
    from bs4 import BeautifulSoup
    doc = BeautifulSoup(res.text)

    d['description']      = quickmeta(doc=doc, name='og:description')
    d['title']            = quickmeta(doc=doc, name='og:title')
    d['thumbnail_url']    = quickmeta(doc=doc, name='og:image:secure_url')
    d['thumbnail_width']  = quickmeta(doc=doc, name='og:image:width')
    d['thumbnail_height'] = quickmeta(doc=doc, name='og:image:width')
    d['provider_name']    = quickmeta(doc=doc, name='twitter:site')

    if not d['description']:
      # get normal desxcription tag.
      tag = doc.html.head.findAll('meta', attrs={"name":"description"})
      if not tag:
        tag = doc.html.head.findAll('meta', attrs={"name":"Description"})

      d['description'] = '' if not tag else u"".join([t['content'] for t in tag])

    if not d['title']:
      d['title'] = doc.html.head.title.text

    if not d['thumbnail_url']:
      d['thumbnail_url'] = quickmeta(doc=doc, name='og:image')


    #import opengraph


    # og = opengraph.OpenGraph(html=res.text)
    # ogd = dict(og.items())
    # print "hehehehehehehehehe"
    # print og.items()
    # d = {
    #   "url": url,
    #   "encoding": res.encoding,
    #   "provider_name":  ogd.get('site_name'),
    #   "title": ogd.get('title'),
    #   "description": ogd.get('description'),
    #   "type": "link",
    #   "html": ''
    # }
    # print ogd
    # if ogd.get('image'):
    #   d.update({
    #     "thumbnail_url" : ogd.get('image'),
    #     "thumbnail_width" : ogd.get('image:width'),
    #     "thumbnail_height" : ogd.get('image:height'),
    #   })

    # if not d['title']:




    cache.set(ckey, d)
    # custom from og
    return Response(d)
