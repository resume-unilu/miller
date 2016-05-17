import json
from rest_framework import serializers,viewsets

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
    # if request.user.is_authenticated():
    #   docs = self.queryset.filter(Q(owner=request.user) | Q(authors=request.user) | Q(status=Story.PUBLIC)).filter(**filters).distinct()
    # else:
    #   docs = self.queryset.filter(story__status=Story.PUBLIC).filter(**filters).distinct()
    
    page    = self.paginate_queryset(docs)

    serializer = DocumentSerializer(docs, many=True,
        context={'request': request}
    )
    return self.get_paginated_response(serializer.data)
