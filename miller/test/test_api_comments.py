import json
from actstream.models import any_stream
from django.test import TestCase
from miller.test import ApiMillerTestCase
from miller.models import Comment

# python manage.py test miller.test.test_api_comments.CommentTest
class CommentTest(ApiMillerTestCase):


  def test_story(self):
    response = self.client_user_A.get('/api/story/%s/' % self.story_A.slug)
    self.assertEqual(response.json()['title'], self.story_A.title)


  def test_create_comment(self):
    # normal user adds a comment to its own story
    response_user_A = self.client_user_A.post('/api/comment/', {
      'story': self.story_A.pk,
      'contents': json.dumps({'content':'This is a very nice comment.'})
    })
    self.assertEqual(response_user_A.status_code, 201)
    self.assertEqual(response_user_A.json()['owner']['username'], self.user_A.username)

    # user_staff adds a comment to normal user story
    response_user_staff = self.client_staff.post('/api/comment/', {
      'story': self.story_A.pk,
      'contents': json.dumps({'content':'I dunno. Are you really sure about what are you writing here? Really?'})
    })
    self.assertEqual(response_user_staff.status_code, 201)
    self.assertEqual(response_user_staff.json()['owner']['username'], self.user_staff.username)

    # an anonymous user? This can't work, not at all!
    response_anonymous = self.client_anonymous.post('/api/comment/', {
      'story': self.story_A.pk,
      'contents': json.dumps({'content':'This is a very nice comment.'})
    })
    self.assertEqual(response_anonymous.status_code, 403)

    # ok let's see what tdo we have here.
    response_user_staff = self.client_staff.get('/api/comment/')
    self.assertEqual(response_user_staff.status_code, 200)
    self.assertEqual(response_user_staff.json()['count'], 2)

    # what does the public see? nothing, since the comments aren't public yet!!!
    response_anonymous = self.client_anonymous.get('/api/comment/')
    self.assertEqual(response_anonymous.status_code, 200)
    self.assertEqual(response_anonymous.json()['count'], 0)


  def test_delete_comment(self):
    """
    Rule: only owner or staff users can delete a comment. Not even coauthors
    """
    response_user_A = self.client_user_A.post('/api/comment/', {
      'story': self.story_A.pk,
      'contents': json.dumps({'content':'This is a very nice comment.'})
    })
    self.assertEqual(response_user_A.status_code, 201)

    com = Comment.objects.get(pk=response_user_A.json()['pk'])

    # get the number of comments
    response_user_A = self.client_user_A.get('/api/comment/')
    self.assertEqual(response_user_A.status_code, 200)
    count = response_user_A.json()['count']

    # try with an anonymoususer
    response_anonymous = self.client_anonymous.delete('/api/comment/%s/'% com.short_url)
    self.assertEqual(response_anonymous.status_code, 403)

    # try with another user
    response_user_B = self.client_user_B.delete('/api/comment/%s/'% com.short_url)
    self.assertEqual(response_user_B.status_code, 404)

    # try with the coauthor! Nothing to do either...
    response_user_C = self.client_user_C.delete('/api/comment/%s/'% com.short_url)
    self.assertEqual(response_user_C.status_code, 404)

    com.refresh_from_db()
    self.assertEqual(com.status, Comment.PRIVATE) # the default is private

    # let the user delete its own comments:
    response_user_A = self.client_user_A.delete('/api/comment/%s/'% com.short_url)
    self.assertEqual(response_user_A.status_code, 204) #no content
    
    com.refresh_from_db()
    self.assertEqual(com.status, Comment.DELETED)

    # get the number of comments
    response_user_A = self.client_user_A.get('/api/comment/')
    self.assertEqual(response_user_A.status_code, 200)
    self.assertEqual(response_user_A.json()['count'], count - 1);

    # get the latest action!!
    action = any_stream(self.user_A).first()

    self.assertEqual(action.verb, 'uncommented')
