import json
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers




class HitField(serializers.Field):
  def to_representation(self, obj):
    return obj

class OptionalFileField(serializers.FileField):
  def to_representation(self, obj):
    if hasattr(obj, 'url'):
      return '%s%s'%(settings.MILLER_HOST, obj.url)
    return None

class JsonField(serializers.Field):
  def to_internal_value(self, data):
    return data

  def to_representation(self, obj):
    if obj:
      try:
        return json.loads(obj)
      except ValueError as e:

        # return u"error: '%s' % e
        
        return obj
      except TypeError as e:
        # return 
        #   "error": u'%s' % e
        # }
        return obj
    return obj


class ContentTypeField(serializers.Field):
  def to_representation(self, obj):
    return ContentType.objects.get_for_model(obj).model


