import json
from actstream.models import any_stream
from django.test import TestCase
from miller.test import ApiMillerTestCase
from miller.models import Comment

# python manage.py test miller.test.test_api_reviews.ReviewTest
class ReviewTest(ApiMillerTestCase):


  def test_story(self):
    response = self.client_user_A.get('/api/story/%s/' % self.story_A.slug)
    self.assertEqual(response.json()['title'], self.story_A.title)


  def test_create_review(self):
    # normal user adds a comment to its own story
    response_user_A = self.client_user_A.post('/api/review/', {
      'story': self.story_A.pk,
      'contents': json.dumps({'content':'This is a very nice comment.'})
    })
    
    self.assertEqual(response_user_A.status_code, 403)

    response_user_staff = self.client_staff.post('/api/review/', {
      'story': self.story_A.pk,
      'assignee': self.user_A.pk
    })

    print response_user_staff.json()
    