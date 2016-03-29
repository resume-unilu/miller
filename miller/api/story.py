from rest_framework import serializers,viewsets
from miller.models import Story

# Serializers define the API representation.
class StorySerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = Story
    fields = ('short-url', 'title')

# ViewSets define the view behavior. Filter by status
class StoryViewSet(viewsets.ModelViewSet):
  queryset = Story.objects.filter(status=Story.PUBLIC)
  serializer_class = StorySerializer