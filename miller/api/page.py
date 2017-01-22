from rest_framework import viewsets
from miller.api.serializers import LitePageSerializer, PageSerializer

from miller.models import Page



class PageViewSet(viewsets.ReadOnlyModelViewSet):
  """
  Model viewset related to Review model.
  Default mixin get, post delete are for admin only.
  """
  queryset = Page.objects.all()
  serializer_class = PageSerializer
  list_serializer_class = LitePageSerializer
  lookup_field = 'slug'
  lookup_value_regex = '[0-9a-zA-Z\-]+'
