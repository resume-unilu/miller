import json

from django.shortcuts import get_object_or_404

from rest_framework import serializers,viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route

from miller.models import Document
from miller.api.serializers import MatchingDocumentSerializer, LiteDocumentSerializer, DocumentSerializer, CreateDocumentSerializer
from miller.api.utils import Glue


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

