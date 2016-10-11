import json

from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import serializers,viewsets
from rest_framework.response import Response

from miller.models import Story, Tag
from serializers import CollectionSerializer

# Collection viewset. A collection is a story which contain other stories inside his content.
# Where should we parse the content?
class CollectionViewSet(viewsets.ModelViewSet):
  queryset = Story.objects.filter(tags__slug=Tag.COLLECTION)
  serializer_class = CollectionSerializer

  # retrieve method
  def retrieve(self, request, *args, **kwargs):
    if request.user.is_authenticated():
      queryset = self.queryset.filter(Q(owner=request.user) | Q(authors=request.user) | Q(status=Story.PUBLIC)).distinct()
    else:
      queryset = self.queryset.filter(status=Story.PUBLIC).distinct()

    if 'pk' in kwargs and not kwargs['pk'].isdigit():
      print 'PK', kwargs['pk']
      story = get_object_or_404(queryset, slug=kwargs['pk'])
    else:
      story = get_object_or_404(queryset, pk=kwargs['pk'])
    
    # resolve attached stories ;)
    serializer = CollectionSerializer(story,
        context={'request': request},
    )
    return Response(serializer.data)
