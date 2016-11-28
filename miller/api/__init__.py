import json
from collection import CollectionViewSet
from story import StoryViewSet
from tag import TagViewSet
from caption import CaptionViewSet
from mention import MentionViewSet
from document import DocumentViewSet
from profile import ProfileViewSet
from comment import CommentViewSet
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets

# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = User
    fields = ('url', 'username', 'email', 'is_staff')

# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
  queryset = User.objects.all()
  serializer_class = UserSerializer


