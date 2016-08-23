import json

from django.shortcuts import get_object_or_404

from rest_framework import serializers,viewsets
from rest_framework.response import Response

from miller.models import Document

class OptionalFileField(serializers.Field):
  def to_representation(self, obj):
    if hasattr(obj, 'url'):
      return obj.url
    return None

class JsonField(serializers.Field):
  def to_representation(self, obj):
    if obj:
      try:
        return json.loads(obj)
      except ValueError:
        return obj
    return obj

# define the 
class CreateDocumentSerializer(serializers.ModelSerializer):
  owner = serializers.HiddenField(
    default=serializers.CurrentUserDefault()
  )

  class Meta:
    model = Document


# Serializers define the API representation.
class DocumentSerializer(serializers.ModelSerializer):
  # authors = AuthorSerializer(many=True)
  # owner = AuthorSerializer()
  # tags = TagSerializer(many=True)
  # captions = CaptionSerializer(source='caption_set', many=True)
  metadata = JsonField(source='contents')
  src   = OptionalFileField(source='attachment')
  class Meta:
    model = Document
    fields = ('id', 'url', 'src', 'metadata', 'type', 'slug', 'title', 'metadata', 'snapshot', 'copyrights')


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
      docs = Document.objects.filter(**filters)
    else:
      docs = Document.objects.filter(**filters)
    
    page    = self.paginate_queryset(docs)
    if page is not None:
      serializer = DocumentSerializer(page, many=True, context={'request': request})
      return self.get_paginated_response(serializer.data)

    serializer = DocumentSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)

