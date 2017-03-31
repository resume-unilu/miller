import json
from author import AuthorViewSet
from review import ReviewViewSet
from collection import CollectionViewSet
from story import StoryViewSet
from tag import TagViewSet
from caption import CaptionViewSet
from mention import MentionViewSet
from document import DocumentViewSet
from profile import ProfileViewSet
from comment import CommentViewSet
from pulse import PulseViewSet
from page import PageViewSet
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from utils import Glue

# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = User
    fields = ('url', 'username', 'email', 'is_staff')

# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
  queryset = User.objects.all()
  serializer_class = UserSerializer
  permission_classes = (IsAdminUser,)


  def list(self, request):
    g = Glue(request=request, queryset=self.queryset)
    print g.filters
    users = g.queryset

    page    = self.paginate_queryset(users)
    serializer = UserSerializer(page, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)