from rest_framework import serializers,viewsets

from miller.api.serializers import CommentSerializer, CreateCommentSerializer
from miller.models import Comment
from rest_framework.response import Response

# ViewSets define the view behavior. Filter by status
class CommentViewSet(viewsets.ModelViewSet):
  queryset = Comment.objects.all()
  serializer_class = CommentSerializer

  """
  you can leave a comment if:
  1. the story is public and opened to comments
  2. you're staff
  3. ths story status is REVIEW and you are a reviewer (story watcher.)
  # """
  def create(self, request, *args, **kwargs):
    serializer = CreateCommentSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    # check if it can be saved for the selected history
    story = serializer.validated_data['story']

    # check if this is public / opened to comments
    
    self.perform_create(serializer)
    headers = self.get_success_headers(serializer.data)
    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


  #   pass