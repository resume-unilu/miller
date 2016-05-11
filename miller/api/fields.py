import json
from rest_framework import serializers


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
      except ValueError:
        return obj
    return obj