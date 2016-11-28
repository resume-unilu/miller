from rest_framework import serializers,viewsets

from miller.api.serializers import CommentSerializer
from miller.models import Comment

# ViewSets define the view behavior. Filter by status
class CommentViewSet(viewsets.ModelViewSet):
  queryset = Comment.objects.all()
  serializer_class = CommentSerializer