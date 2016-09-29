import json
from rest_framework import serializers

class HitField(serializers.Field):
  def to_representation(self, obj):
    return obj

class OptionalFileField(serializers.Field):
  def to_representation(self, obj):
    if hasattr(obj, 'url'):
      return obj.url
    return None

class JsonField(serializers.Field):
  def to_representation(self, obj):
    if obj:
      try:
        return json.loads(obj)
      except ValueError as e:

        return {
          "error": u'%s' % e
        }
        return obj
    return obj