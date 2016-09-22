import json

from django.shortcuts import get_object_or_404

from rest_framework import serializers,viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route

from miller.models import Document
from miller.api.serializers import MatchingDocumentSerializer, DocumentSerializer, CreateDocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
  queryset = Document.objects.all()
  serializer_class = CreateDocumentSerializer

  # retrieve by PK or slug
  def retrieve(self, request, *args, **kwargs):
    if 'pk' in kwargs and not kwargs['pk'].isdigit():
      doc = get_object_or_404(Document, slug=kwargs['pk'])  
      # save, then return tagged items according to tagform
      serializer = DocumentSerializer(doc,
          context={'request': request},
      )
      return Response(serializer.data)
    
    return super(DocumentViewSet, self).retrieve(request, *args, **kwargs)
    

  def list(self, request):
    filters = self.request.query_params.get('filters', None)
    
    if filters is not None:
      print filters
      try:
        filters = json.loads(filters)
        print "filters,",filters
      except Exception, e:
        print e
        filters = {}
    else:
      filters = {}
    
    if request.user.is_authenticated():
      docs = Document.objects.filter(**filters).distinct()
    else:
      docs = Document.objects.filter(**filters).distinct()
    
    page    = self.paginate_queryset(docs)
    if page is not None:
      serializer = DocumentSerializer(page, many=True, context={'request': request})
      return self.get_paginated_response(serializer.data)

    serializer = DocumentSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


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

