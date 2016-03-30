from rest_framework import serializers,viewsets
from miller.models import Tag, Story
from rest_framework.decorators import api_view

# story serializer for tags
class StorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Tag
    fields = ('url', 'title', 'date')

# Serializers define the API representation.
class TagSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = Tag
    fields = ('url','name', 'category')
    

# ViewSets define the view behavior. Filter by status
class TagViewSet(viewsets.ModelViewSet):
  stories = StorySerializer(many=True)

  queryset = Tag.objects.all()
  serializer_class = TagSerializer

