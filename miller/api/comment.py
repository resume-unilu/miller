from django.db.models import Q
from rest_framework import serializers,viewsets, status

from miller.api.serializers import CommentSerializer, CreateCommentSerializer
from miller.models import Comment
from miller.api.utils import Glue
from rest_framework.response import Response

# ViewSets define the view behavior. Filter by status
class CommentViewSet(viewsets.ModelViewSet):
  queryset = Comment.objects.all()
  serializer_class = CommentSerializer

  def _getUserAuthorizations(self, request):
    if request.user.is_staff:
      q = self.queryset
    elif request.user.is_authenticated:
      q = self.queryset.filter(Q(owner=request.user) | Q(status=Comment.PUBLIC) | Q(story__authors__user=request.user)).distinct()
    else:
      q = self.queryset.filter(status=Comment.PUBLIC).distinct()
    return q

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
    # // reserialize

    return Response(CommentSerializer(instance=serializer.instance).data, status=status.HTTP_201_CREATED, headers=headers)


  def list(self, request):
    coms = self._getUserAuthorizations(request)
    g = Glue(request=request, queryset=coms)
    
    coms = g.queryset

    # add orderby

    # print coms.query
    page    = self.paginate_queryset(coms)
    
    serializer = CommentSerializer(page, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)

  #  pass