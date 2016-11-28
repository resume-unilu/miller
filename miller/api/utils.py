import json
from django.contrib.contenttypes.models import ContentType

# usage in viewsets.ModelViewSet methods, e;g. retrieve: 
# filters = filtersFromRequest(request=self.request) 
# qs = stories.objects.filter(**filters).order_by(*ordering)
def filtersFromRequest(request):
  filters = request.query_params.get('filters', None)
    
  if filters is not None:
    try:
      filters = json.loads(filters)
      # print "filters,",filters
    except Exception, e:
      # print e
      filters = {}
  else:
    filters = {}

  return filters


# usage in viewsets.ModelViewSet methods, e;g. retrieve: 
# ordering = orderingFromRequest(request=self.request) 
# qs = stories.objects.all().order_by(*ordering)
def orderingFromRequest(request):
  ordering = request.query_params.get('ordering', None)
  return ordering.split(',') if ordering is not None else None

# get corresponding serializer class to content_type.model property. `content_type` is instance of django.contrib.contenttypes.models.ContentType 
# https://docs.djangoproject.com/en/1.10/ref/contrib/contenttypes/#django.contrib.contenttypes.models.ContentType  
def get_serializer(content_type):
  # map of model names / serializers class
  if content_type.model == 'user':
    from miller.api.serializers import UserSerializer
    serializer = UserSerializer
  elif content_type.model == 'document':
    from miller.api.serializers import LiteDocumentSerializer
    serializer = LiteDocumentSerializer
  elif content_type.model == 'story':
    from miller.api.serializers import LiteStorySerializer
    serializer = LiteStorySerializer
  elif content_type.model == 'profile':
    from miller.api.serializers import ProfileSerializer
    serializer = ProfileSerializer
  elif content_type.model == 'comment':
    from miller.api.serializers import CommentSerializer
    serializer = CommentSerializer
  if not serializer:
    # raise
    return None
  return serializer


def get_serialized(instance):
  content_type  = ContentType.objects.get_for_model(instance)
  serializer = get_serializer(content_type)
  if serializer is None:
    return None
  return serializer(instance).data