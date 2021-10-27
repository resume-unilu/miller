from actstream.models import Action
from django.contrib.auth.models import User, Group
from rest_framework import serializers, validators
from miller.models import Profile, Document, Tag, Story, Caption, Mention, Author, Comment, Review, Page, StoryHit
from miller.api.fields import JsonField, HitField, OptionalFileField, ContentTypeField, IfJsonField
from miller.api import utils



class CaptionSerializer(serializers.HyperlinkedModelSerializer):
  document_id    = serializers.ReadOnlyField(source='document.id')
  type  = serializers.ReadOnlyField(source='document.type')
  title = serializers.ReadOnlyField(source='document.title')
  slug  = serializers.ReadOnlyField(source='document.slug')
  url   = serializers.ReadOnlyField(source='document.url')
  src   = OptionalFileField(source='document.attachment')
  short_url = serializers.ReadOnlyField(source='document.short_url')
  copyrights = serializers.ReadOnlyField(source='document.copyrights')
  caption = serializers.ReadOnlyField(source='contents')
  data = JsonField(source='document.data')
  snapshot   = OptionalFileField(source='document.snapshot', read_only=True)
  attachment = OptionalFileField(source='document.attachment', read_only=True)

  class Meta:
    model = Caption
    fields = ('id', 'document_id', 'title', 'slug', 'url', 'type', 'copyrights', 'caption', 'short_url', 'src', 'snapshot', 'attachment', 'data')


class UserSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ('id', 'username', 'email', 'is_staff')


class UserGroupSerializer(serializers.ModelSerializer):
  class Meta:
    model = Group
    fields = ('id', 'name')

class CommentSerializer(serializers.ModelSerializer):
  contents = JsonField()
  owner    = UserSerializer()
  
  class Meta:
    model = Comment
    fields = ('pk', 'owner', 'contents', 'version', 'date_created', 'highlights', 'short_url', 'status')


class ActionCommentSerializer(serializers.ModelSerializer):
  owner    = UserSerializer()
  class Meta:
    model = Comment
    fields = ('pk', 'owner', 'version')


# tag represnetation in many to many
class TagSerializer(serializers.ModelSerializer):

  stories = serializers.IntegerField(read_only=True, source='num_stories')
  created = serializers.BooleanField(read_only=True, source='is_created')

  class Meta:
    model = Tag
    fields = ('id', 'category', 'slug', 'name', 'status', 'data', 'stories', 'created', 'usage_statistics')

  def run_validators(self, value):
    for validator in self.validators:
      if isinstance(validator, validators.UniqueTogetherValidator):
          self.validators.remove(validator)
    super(TagSerializer, self).run_validators(value)

  def create(self, validated_data):
    instance, created = Tag.objects.get_or_create(name=validated_data['name'].lower(), category=validated_data['category'], defaults={'data': validated_data['data']})
    instance.is_created = created
    return instance



class ProfileSerializer(serializers.ModelSerializer):
  """
  Base serializer for Profile model instances.
  """  
  user = UserSerializer()
  username    = serializers.ReadOnlyField(source='user.username')
  
  class Meta:
    model = Profile
    lookup_field = 'user__username'
    fields = ('id', 'bio', 'picture', 'username', 'user', 'newsletter')





class LiteAuthorSerializer(serializers.ModelSerializer):
  """
  lite Serializer for an author, i.e. without profile info.
  """
  stories = serializers.IntegerField(read_only=True, source='num_stories')

  class Meta:
    model = Author
    fields = ('id', 'fullname', 'affiliation', 'data', 'slug', 'stories')



class AuthorSerializer(LiteAuthorSerializer):
  """
  Serializer for an author
  """
  profile = ProfileSerializer(source='user.profile')
  
  class Meta:
    model = Author
    fields = ('id', 'profile', 'fullname', 'affiliation', 'data', 'slug')


class HeavyProfileSerializer(ProfileSerializer):
  """
  This serializer is used in miller.context_processors !!!
  Double check when modify this.
  """
  authors = LiteAuthorSerializer(many=True, source='user.authorship')
  groups = UserGroupSerializer(many=True, source= 'user.groups')

  class Meta:
    model = Profile
    lookup_field = 'user__username'
    fields = ('pk', 'bio', 'picture', 'username', 'authors', 'groups', 'newsletter')


############
# Document #
############

class LiteDocumentSerializer(serializers.ModelSerializer):
  """
  # light document serializer (to be used in manytomany retrieve)
  """
  snapshot = OptionalFileField()
  attachment = OptionalFileField()
  class Meta:
    model = Document
    fields = ('id', 'title', 'slug', 'mimetype', 'type', 'data', 'url', 'attachment', 'snapshot')



# Serializers define the API representation.
class DocumentSerializer(LiteDocumentSerializer):
  src   = OptionalFileField(source='attachment')
  documents = LiteDocumentSerializer(many=True)

  class Meta:
    model = Document
    fields = ('id', 'url', 'src',  'data', 'type', 'slug', 'title', 'snapshot', 'copyrights', 'attachment', 'documents', 'locked')


class MatchingDocumentSerializer(serializers.ModelSerializer):
  matches = HitField()
  src   = OptionalFileField(source='attachment')

  class Meta:
    model = Document
    fields = ('id', 'url', 'src', 'data', 'type', 'slug', 'title', 'matches')


# define the 
class CreateDocumentSerializer(serializers.ModelSerializer):
  owner = serializers.HiddenField(
    default=serializers.CurrentUserDefault()
  )
  snapshot = OptionalFileField(read_only=True)
  attachment = OptionalFileField(required=False)

  class Meta:
    model = Document
    fields = ('id', 'owner', 'type', 'data', 'short_url', 'title', 'slug', 'copyrights', 'url', 'attachment', 'snapshot', 'mimetype')
  



class LiteMentionSerializer(serializers.ModelSerializer):
  slug     = serializers.ReadOnlyField()
  data     = JsonField()
  covers   = LiteDocumentSerializer(many=True)
  tags     = TagSerializer(many=True)
  authors  = AuthorSerializer(many=True)
  status   = serializers.ReadOnlyField(source='to_story.status')

  class Meta:
    model = Mention
    fields = ('id', 'slug', 'data', 'tags', 'authors', 'covers', 'status')


# Story Serializer to use in action lists
class IncrediblyLiteStorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Story
    fields = ('id', 'short_url', 'slug', 'title', 'status', 'version')



# Story Serializer to use in lists
class AnonymousLiteStorySerializer(serializers.ModelSerializer):
  tags     = TagSerializer(many=True)
  covers   = LiteDocumentSerializer(many=True)
  source   = serializers.BooleanField(source='isSourceAvailable')

  class Meta:
    model = Story
    fields = ('id', 'slug', 'short_url', 'date',  'version', 'date_created', 'date_last_modified', 'status', 'covers', 'tags',  'data', 'source')


# Story Serializer to use in lists
class LiteStorySerializer(AnonymousLiteStorySerializer):
  authors = AuthorSerializer(many=True)
  owner = UserSerializer()
  
  class Meta:
    model = Story
    fields = ('id', 'slug', 'short_url', 'date',  'date_created', 'date_last_modified', 'status', 'covers', 'authors', 'tags', 'owner',  'data')



# retrieve a Story, full
class StorySerializer(LiteStorySerializer):
  documents  = CaptionSerializer(source='caption_set', many=True)
  stories    = LiteMentionSerializer(many=True)
  contents   = IfJsonField()
  hitcount = serializers.SerializerMethodField()

  def get_hitcount(self, story):
    story_hits = StoryHit.objects.filter(story=story)
    try:
      read = story_hits.get(action=StoryHit.VIEWED).hits
    except StoryHit.DoesNotExist:
      read = None

    try:
      download = story_hits.get(action=StoryHit.DOWNLOADED).hits
    except StoryHit.DoesNotExist:
      download = None

    return {'read': read, 'download': download}

  class Meta:
    model = Story
    fields = (
      'id','url','slug','short_url',
      'title', 'abstract',
      'documents', 'tags', 'covers', 'stories',
      'data',
      'contents',
      'date', 'date_created', 'date_last_modified',
      'status', 
      'source',
      'authors','owner',
      'highlights',
      'version',
      'hitcount'
    )



class AnonymousStorySerializer(AnonymousLiteStorySerializer):
  """
  Retrive a full stry instance, but anonymous
  """
  documents = CaptionSerializer(source='caption_set', many=True)
  stories = LiteMentionSerializer(many=True)
  contents   = IfJsonField()
  
  class Meta:
    model = Story
    fields = (
      'id','url','slug','short_url',
      'title', 'abstract',
      'documents', 'tags', 'covers', 'stories',
      'data',
      'contents',
      'date', 'date_created', 
      'status','owner',
      'source',
      'highlights'
    )


# Story serializer containing whoosh matches
class MatchingStorySerializer(serializers.HyperlinkedModelSerializer):
  authors = AuthorSerializer(many=True)
  owner = UserSerializer()
  tags = TagSerializer(many=True)
  covers = LiteDocumentSerializer(many=True)
  matches = HitField()

  def is_named_bar(self, foo):
      return foo.name == "bar" 

  class Meta:
    model = Story
    fields = ('id', 'url', 'slug', 'short_url', 'title', 'abstract', 'date',  'date_created', 'status', 'covers', 'data', 'authors', 'tags', 'owner', 'matches')



# Serializer when creating stories. It automatically add the owner as author
class CreateStorySerializer(serializers.ModelSerializer):
  class Meta:
    model  = Story
    exclude = ('owner',)



# Serializer when creating stories. It automatically add the owner as author
class CreateCommentSerializer(serializers.ModelSerializer):
  owner = serializers.HiddenField(
    default=serializers.CurrentUserDefault()
  )

  def validate_contents(self, value):
    """
    Check that Json contents is actually JSON content and it contains something
    """
    import json
    try:
      _value = json.loads(value)
      if not 'content' in _value:
        raise serializers.ValidationError("contents JSON should contain a 'content' property.")
      if not _value['content']:
        raise serializers.ValidationError("contents JSON should contain a 'content' property.")
      
    except Exception as e:
      raise serializers.ValidationError("contents field should contain a valid JSON text")
    return value

  class Meta:
    model  = Comment
    fields = '__all__'


##############
# Collection #
##############

# A story of stories
class CollectionSerializer(serializers.ModelSerializer):
  authors = AuthorSerializer(many=True)
  stories = LiteMentionSerializer(many=True)
  owner = UserSerializer()
  tags = TagSerializer(many=True)
  covers = LiteDocumentSerializer(many=True)
  documents = CaptionSerializer(source='caption_set', many=True)


  class Meta:
    model = Story
    fields = ('id', 'status', 'slug', 'title', 'covers', 'authors', 'owner', 'tags', 'documents', 'stories', 'data', 'contents')





  # def create(self, validated_data):
  #   print 'CREATING', validated_data

  #   # owner =  validated_data.pop('owner')
  #   # print owner.id
  #   if not 'url' in validated_data:
  #     return super(CreateDocumentSerializer, self).create(validated_data)

  #   print 'url:', validated_data['url']
  #   # get object
  #   try:
  #     doc = Document.objects.get(url=validated_data['url'])
  #   except Document.DoesNotExist:
  #     print "not found, create"
  #     return super(CreateDocumentSerializer, self).create(validated_data)
  #   else:
  #     return doc
    # print "found doc", doc
    # instance, _ = Document.objects.get_or_create(url=validated_data['url'], defaults=validated_data)
    
    # return instance
    
    

############
# Mentions #
############
class MentionSerializer(serializers.ModelSerializer):
  to_story = LiteStorySerializer()
  from_story     = LiteStorySerializer()

  class Meta:
    model = Mention
    fields = ('id', 'to_story', 'from_story')


############
# Reviews  #
############
class LiteReviewSerializer(serializers.ModelSerializer):
  """
  list of currernt reviews and their status
  """
  assignee = UserSerializer()
  story = AnonymousLiteStorySerializer()
  class Meta:
    model = Review
    fields = ('id', 'contents', 'category', 'status', 'assignee', 'due_date', 'score', 'story')


class ReviewSerializer(LiteReviewSerializer):
  """
  Single review. It ships the related story with full serializer.
  """
  story = AnonymousStorySerializer()
  class Meta:
    model = Review
    fields = ('id', 'contents', 'category', 'status', 'assignee', 'due_date', 'story', 'thematic','thematic_score','interest', 'interest_score', 'originality', 'originality_score', 'innovation', 'innovation_score', 'interdisciplinarity', 'interdisciplinarity_score', 'methodology_score', 'methodology', 'clarity', 'clarity_score', 'argumentation_score', 'argumentation',
      'structure_score','structure', 'references', 'references_score', 'pertinence','pertinence_score')


class CreateReviewSerializer(serializers.ModelSerializer):
  assigned_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
  
  class Meta:
    model  = Review
    fields = ('id', 'story', 'assignee', 'assigned_by', 'contents', 'category', 'status', 'due_date')



class AnonymousReviewSerializer(serializers.ModelSerializer):
  """
  Single review report, without assignee nor private comments. It ships the related story with full serializer.
  """
  story = AnonymousStorySerializer()
  class Meta:
    model = Review
    fields = ('id', 'contents', 'category', 'status', 'due_date', 'story', 'thematic','thematic_score','interest', 'interest_score', 'originality', 'originality_score', 'innovation', 'innovation_score', 'interdisciplinarity', 'interdisciplinarity_score', 'methodology_score', 'methodology', 'clarity', 'clarity_score', 'argumentation_score', 'argumentation',
      'structure_score','structure', 'references', 'references_score', 'pertinence','pertinence_score')



class AnonymousLiteReviewSerializer(serializers.ModelSerializer):
  """
  list of currernt reviews and their status
  """
  story = AnonymousLiteStorySerializer()

  class Meta:
    model = Review
    fields = ('id', 'contents', 'category', 'status', 'due_date', 'score', 'story') + Review.FIELDS_FOR_SCORE


class LiteReviewWithoutStorySerializer(serializers.ModelSerializer):
  assignee = UserSerializer()
  
  class Meta:
    model = Review
    fields = ('id', 'category', 'contents', 'status', 'due_date', 'score', 'assignee')



class ActionSerializer(serializers.ModelSerializer):
  """
  Generic serializer
  """
  class IncredibleField(serializers.RelatedField):
    def to_representation(self, value):
      if isinstance(value, User):
        serializer = UserSerializer(value)
      elif isinstance(value, Document):
        serializer = LiteDocumentSerializer(value)
      elif isinstance(value, Story):
        serializer = IncrediblyLiteStorySerializer(value)
      elif isinstance(value, Profile):
        serializer = ProfileSerializer(value)
      elif isinstance(value, Comment):
        serializer = CommentSerializer(value)
      else:
        raise Exception('Unexpected type of action object')
      return serializer.data

  actor  = IncredibleField(read_only=True)
  target = IncredibleField(read_only=True)
  target_content_type = ContentTypeField(source='target', read_only=True)
  info = JsonField(source='data')

  class Meta:
    model = Action
    fields = ('id', 'verb', 'description', 'timestamp', 'timesince', 'actor', 'target', 'target_content_type', 'info') #, 'actor', 'target')



class PageSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = Page
    fields = ('id', 'name', 'slug', 'contents', 'url') #, 'actor', 'target')
    extra_kwargs = {
      'url': {
        'lookup_field': 'slug'
      }
    }


class LitePageSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = Page
    fields = ('id', 'name', 'slug', 'url') #, 'actor', 'target')
    extra_kwargs = {
      'url': {
        'lookup_field': 'slug'
      }
    }


# Story Serializer, with review to use in lists
class PendingStorySerializer(serializers.ModelSerializer):
  tags = TagSerializer(many=True)
  covers = LiteDocumentSerializer(many=True)
  reviews = LiteReviewWithoutStorySerializer(many=True)
  class Meta:
    model = Story
    fields = ('id', 'slug', 'short_url', 'date',  'date_created', 'date_last_modified', 'status', 'covers', 'tags',  'data', 'reviews')



