import os, json, requests, mimetypes

from django.core.cache import cache
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import serializers,viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.exceptions import ValidationError, PermissionDenied, ParseError, NotFound
from rest_framework.response import Response

from miller.models import Document
from miller.forms import URLForm, SearchQueryForm
from miller.api.serializers import MatchingDocumentSerializer, LiteDocumentSerializer, DocumentSerializer, CreateDocumentSerializer
from miller.api.utils import Glue, filters_from_request

from requests.exceptions import HTTPError, Timeout
from .pagination import FacetedPagination

from wsgiref.util import FileWrapper

from django.conf import settings
from django.utils.module_loading import import_string
DOCUMENT_LIST_SERIALIZER = getattr(settings, 'DOCUMENT_LIST_SERIALIZER', 'miller.api.serializers.LiteDocumentSerializer')
list_serializer_class = import_string(DOCUMENT_LIST_SERIALIZER)

class DocumentViewSet(viewsets.ModelViewSet):
  queryset = Document.objects.all().prefetch_related('documents')
  serializer_class = CreateDocumentSerializer
  list_serializer_class = list_serializer_class
  pagination_class = FacetedPagination


  @detail_route(methods=['get'])
  def download(self, request, pk):
    """
    Given a document pk, download as ZIP files a data file descriptor + text file data format.
    """
    doc = get_object_or_404(self.queryset, pk=pk)
    # create ZIP containing the media (if available) and the text document
    attachment = doc.download(outputFormat='iiif')
    # should be ZIP
    mimetype = mimetypes.guess_type(attachment)[0]

    response = StreamingHttpResponse(FileWrapper( open(attachment), 8192), content_type=mimetype)
    response['Content-Length'] = os.path.getsize(attachment)
    response['Content-Disposition'] = 'attachment; filename="%s.%s"' % (doc.slug, mimetypes.guess_extension(mimetype))

    return response

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
    Add matches to the list of matching document.
    /api/document/?q=world
    cfr. utils.Glue class
    """
    from miller.forms import SearchQueryForm
    from miller.helpers import search_whoosh_index_headline
    form = SearchQueryForm(request.query_params)
    if not form.is_valid():
      return Response(form.errors, status=status.HTTP_201_CREATED)

    # get the results
    g = Glue(request=request, queryset=self.queryset)

    # queryset = g.queryset.annotate(matches=RawSQL("SELECT
    page    = self.paginate_queryset(g.queryset.distinct())

    # get hort_url to get results out of whoosh
    highlights = search_whoosh_index_headline(query=form.cleaned_data['q'], paths=map(lambda x:x.short_url, page))

    def mapper(d):
      d.matches = []
      for hit in highlights:
        if d.short_url == hit['short_url']:
          d.matches = hit
          break
      return d

    serializer = MatchingDocumentSerializer(map(mapper, page), many=True,
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

    g = Glue(request=request, queryset=self.queryset, perform_q=False)

    ckey = g.get_hash(request=request)
    print ckey
    if cache.has_key(ckey):
      return Response(cache.get(ckey))

    from django.contrib.postgres.search import SearchVector
    from django.contrib.postgres.search import TrigramSimilarity
    # provided a q


    queryset = g.queryset.annotate(
      similarity=TrigramSimilarity('ngrams__segment', form.cleaned_data['q']),
    ).filter(similarity__gt=0.35).order_by('-similarity').values_list('ngrams__segment', flat=True).distinct()[:5]
    # SELECT DISTINCT "miller_ngrams"."segment",
    #     SIMILARITY("miller_ngrams"."segment", europeenne)
    #     FROM "miller_document" LEFT OUTER JOIN "miller_ngrams_documents"
    #     ON ("miller_document"."id" = "miller_ngrams_documents"."document_id")
    #     LEFT OUTER JOIN "miller_ngrams"
    #     ON ("miller_ngrams_documents"."ngrams_id" = "miller_ngrams"."id")
    #     WHERE SIMILARITY("miller_ngrams"."segment", europeenne) > 0.25
    # ORDER BY SIMILARITY("miller_ngrams"."segment", europeenne)
    # DESC LIMIT 20
    # print queryset.query
    d = {
      'results': queryset
    }

    cache.set(ckey, d)
    d.update({
      'cached': False
    })
    return Response(d)



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

    # check if there is no document in the archive matching the url.
    url = form.cleaned_data['url']



    ckey = 'oembed:%s' % url

    if not request.query_params.get('nocache', None) and cache.has_key(ckey):
      return Response(cache.get(ckey))

    # not done? perform requests etc...
    from miller.embedder import custom_noembed, perform_request

    # only top part of the content to get metadata.
    res = perform_request(url, headers={'Range':'bytes=0-20000'})
    content_type  = res.headers.get('content-type', '').split(';')[0]
    provider_url = self.headers.get('Host', None)

    if not provider_url:
      from urlparse import urlparse
      o = urlparse(url)
      provider_url = o.netloc

    # enable smart oembedding. cfr settings.MILLER_OEMBEDS_MAPPER
    e = custom_noembed(url=url, content_type=content_type, provider_url=provider_url)

    if e:
      cache.set(ckey, e)
      return Response(e)
      # is it an image or similar?
      # https://www.hdg.de/lemo/img_hd/bestand/objekte/biografien/schaeuble-wolfgang_foto_LEMO-F-5-051_bbst.jpg

    import micawber
    try:
      providers = micawber.bootstrap_basic()
      d = providers.request(url)

    # check noembed! e.g; for flickr. We should check if the url is in the pattern specified.
    # noembed = perform_request('https://noembed.com/embed', params={
    #   'url': url
    # });
    # d = noembed.json()
    except Exception as e:
      # logger.exception(e)
      # Normally: provider not found
      d = {
        'error': 'unknown',
        'errorDetails': '%s' %e,
        "url": url,
        "encoding": res.encoding,
        #"provider_name":  ogd.get('site_name'),
        #"description": ogd.get('description'),
        "type": "link",
        "html": ''
      }
    else:
      return Response(d)

    # if not 'error' in d:
    #   d.update({
    #     "info": {
    #       'service': 'noembed'
    #     }
    #   })
    #   return Response(d)


    # return Response(d)

    def quickmeta(doc, name, attrs={}, key='name'):
      attrs = {
        key: name
      } if not attrs else attrs
      try:
        m = doc.html.head.findAll('meta', attrs=attrs)
      except AttributeError:
        return None
      #print m, attrs
      return None if not m else u"".join(filter(None, [t.get('content', None) for t in m]))



    # get opengraph data
    from bs4 import BeautifulSoup
    doc = BeautifulSoup(res.text)

    d['description']      = quickmeta(doc=doc, name='og:description')
    d['title']            = quickmeta(doc=doc, name='og:title')
    d['thumbnail_url']    = quickmeta(doc=doc, name='og:image:secure_url')
    d['thumbnail_width']  = quickmeta(doc=doc, name='og:image:width')
    d['thumbnail_height'] = quickmeta(doc=doc, name='og:image:height')
    d['provider_name']    = quickmeta(doc=doc, name='twitter:site')

    if not d['description']:
      # get normal desxcription tag.
      tag = None
      try:
        tag = doc.html.head.findAll('meta', attrs={"name":"description"})
        if not tag:
          tag = doc.html.head.findAll('meta', attrs={"name":"Description"})
      except AttributeError:
        pass

      d['description'] = '' if not tag else u"".join([t['content'] for t in tag])

    if not d['title']:

      try:
        d['title'] = doc.html.head.title.text
      except AttributeError:
        pass

    if not d['thumbnail_url']:
      d['thumbnail_url'] = quickmeta(doc=doc, name='og:image')

    if not d['thumbnail_url']:
      d['thumbnail_url'] = quickmeta(doc=doc, name='og:image', key='property')

    if not d['provider_name']:
      d['provider_name'] = quickmeta(doc=doc, name='og:site_name', key='property')

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
    print d



    cache.set(ckey, d)
    # custom from og
    return Response(d)
