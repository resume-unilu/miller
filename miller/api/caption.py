import json
from rest_framework import serializers, viewsets, status
from rest_framework.response import Response
from miller.api.fields import OptionalFileField, JsonField
from miller.models import Document, Story, Caption


class DocumentSerializer(serializers.ModelSerializer):
  class Meta:
    model = Document
    lookup_field = 'slug'
    fields = ('slug',)

# Serializers define the API representation.
class CaptionSerializer(serializers.ModelSerializer):
  document = DocumentSerializer()
  
  class Meta:
    model = Caption
    fields = ('document', 'story', 'date_created')
    

class NestedCaptionSerializer(serializers.HyperlinkedModelSerializer):
  document_id    = serializers.ReadOnlyField(source='document.id')
  type  = serializers.ReadOnlyField(source='document.type')
  title = serializers.ReadOnlyField(source='document.title')
  slug  = serializers.ReadOnlyField(source='document.slug')
  src   = OptionalFileField(source='document.attachment')
  short_url = serializers.ReadOnlyField(source='document.short_url')
  copyrights = serializers.ReadOnlyField(source='document.copyrights')
  caption = serializers.ReadOnlyField(source='contents')
  metadata = JsonField(source='document.contents')
  snapshot = serializers.ReadOnlyField(source='document.snapshot')

  class Meta:
    model = Caption
    fields = ('id', 'document_id', 'title', 'slug', 'type', 'copyrights', 'caption', 'short_url', 'src', 'snapshot', 'metadata')


# ViewSets define the view behavior. Filter by status
class CaptionViewSet(viewsets.ModelViewSet):

  queryset = Caption.objects.all()
  serializer_class = CaptionSerializer

  def create(self, request, *args, **kwargs):
    # get the document id from the slug
    # print request.data

    doc = Document.objects.get(slug=request.data['document']['slug']);
    story = Story.objects.get(pk=request.data['story'])

    # Create the book instance
    caption, created = Caption.objects.get_or_create(document=doc, story=story)
    # print caption, created

    serializer = NestedCaptionSerializer(caption)
    return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    #return caption

