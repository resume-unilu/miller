from rest_framework import serializers,viewsets


from django.shortcuts import get_object_or_404

from miller.api.serializers import AuthorSerializer
from miller.models import Author

from rest_framework.response import Response


class AuthorViewSet(viewsets.ModelViewSet):
  """
  Author view set api.
  Author request can be handled in two ways: with an author ID, 
  useful for updating etc.. or with 
  the user username. In this case, since we can have multiple 
  authors identities per user, we provide aliases. Cfr api.serializers.AuthorWithAliasesSerializer

  """
  queryset = Author.objects.all()
  serializer_class = AuthorSerializer
  # lookup_field = 'pk'
  # lookup_value_regex = '[0-9a-zA-Z\.-_]+'

  def _getAuthorizedQueryset(self, request):
    if request.user.is_staff:
      q = Author.objects.all()
    elif request.user.is_authenticated():
      q = Story.objects.filter(Q(owner=request.user) | Q(status=Story.PUBLIC) | Q(authors__user=request.user)).distinct()
    else:
      q = Author.objects.filter(status=Story.PUBLIC)
    return q


  def retrieve(self, request, *args, **kwargs):
    if 'pk' in kwargs and not kwargs['pk'].isdigit():
      # by author.slug
      author = get_object_or_404(Author, slug=kwargs['pk'])
    else:
      # by author.pk
      author = get_object_or_404(Author, pk=kwargs['pk'])
    
    serializer = AuthorSerializer(author, context={'request': request})
    return Response(serializer.data)