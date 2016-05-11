import json
from rest_framework import serializers,viewsets
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
    

# ViewSets define the view behavior. Filter by status
class CaptionViewSet(viewsets.ModelViewSet):

  queryset = Caption.objects.all()
  serializer_class = CaptionSerializer

  def create(self, request, *args, **kwargs):
    # get the document id from the slug
    print request.data

    doc = Document.objects.get(slug=request.data['document']['slug']);
    story = Story.objects.get(pk=request.data['story'])

    # Create the book instance
    caption, created = Caption.objects.get_or_create(document=doc, story=story)
    print caption, created

    #return caption

