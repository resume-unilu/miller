from django.shortcuts import get_object_or_404


from rest_framework import serializers,viewsets
from rest_framework.exceptions import NotAuthenticated
from rest_framework.decorators import detail_route, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from miller.api.serializers import ReviewSerializer, LiteReviewSerializer
from miller.models import Review, Author



class ReviewViewSet(viewsets.ModelViewSet):
  """
  Model viewset related to Review model.
  Default mixin get, post delete are for admin only.
  """
  queryset = Review.objects.all()
  serializer_class = ReviewSerializer
  permission_classes = (IsAuthenticated,)

  def _getUserAuthorizations(self, request):
    if request.user.is_staff:
      q = self.queryset.all()
    elif request.user.is_authenticated():
      q = self.queryset.filter(assignee=request.user).distinct()
    else:
      raise Exception('user should be authenticated')
    return q


  #@permission_classes(IsAdminUser)
  def create(self, request, *args, **kwargs):
    """
    Only staff can create reviews
    """
    if not request.user.is_staff:
      # it seems that the permission_classes is not working
      #       @permission_classes((IsAdminUser,))
      # TypeError: 'tuple' object is not callable
      raise NotAuthenticated()
    super(ReviewViewSet, self).create(self, request, *args, **kwargs)


  #@permission_classes(IsAuthenticated)
  def partial_update(self, request, pk, *args, **kwargs):
    """
    Request user can partial update reviews
    """
    pass

  
  def list(self, request, *args, **kwargs):
    """
    This is the list of your reviews. Access to the uncompleted list via todo
    """
    page    = self.paginate_queryset(self.queryset.filter(assignee=request.user))
    serializer = LiteReviewSerializer(self.queryset, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)

  
  def retrieve(self, request, *args, **kwargs):
    """
    List the reviews assigned to the request user. It requires an authentified user.
    """
    review = get_object_or_404(self.queryset.filter(assignee=request.user), pk=kwargs['pk'])
    
    serializer = ReviewSerializer(review,
        context={'request': request},
    )
    return Response(serializer.data)