from django.contrib.auth.models import User
from rest_framework import serializers
from miller.models import Profile

class UserSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ('username', 'first_name', 'last_name', 'is_staff')


# story serializer for tags
class ProfileSerializer(serializers.ModelSerializer):
  user = UserSerializer()
  username    = serializers.ReadOnlyField(source='user.username')
  
  class Meta:
    model = Profile
    lookup_field = 'user__username'
    fields = ('bio', 'picture', 'username', 'user')