
from rest_framework import serializers,viewsets
from miller.models import Story, Tag
from serializers import CollectionSerializer
# Collection viewset. A collection is a story which contain other stories inside his content.
# Where should we parse the content?
class CollectionViewSet(viewsets.ModelViewSet):
  queryset = Story.objects.filter(tags__category=Tag.COLLECTION)
  serializer_class = CollectionSerializer
