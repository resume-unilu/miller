import json
from actstream.models import any_stream
from django.core import mail
from django.test import TestCase
from miller.test import ApiMillerTestCase
from miller.models import Review, Story

# python manage.py test miller.test.test_api_reviews.ReviewTest
class ReviewTest(ApiMillerTestCase):


  def _test_chief_reviewer_can_access_story(self):
    response_client_A = self.client_user_A.get('/api/story/%s/' % self.story_A.slug)
    self.assertEqual(response_client_A.status_code, 200)
    self.assertEqual(response_client_A.json()['status'], Story.DRAFT)
    
    # chief reviewers CANNOT access DRAFTS.
    self.assertEqual(self.user_D.groups.filter(name=Review.GROUP_CHIEF_REVIEWERS).exists(), True)
    response_client_D = self.client_user_D.get('/api/story/%s/' % self.story_A.slug)
    self.assertEqual(response_client_D.status_code, 404)


  def _test_create_editing_review(self):
    # normal user adds a comment to its own story
    response_user_A = self.client_user_A.post('/api/review/', {
      'story': self.story_A.pk,
      'contents': json.dumps({'content':'This is a very nice comment.'})
    })
    
    self.assertEqual(response_user_A.status_code, 403)

    # Empty the test outbox
    mail.outbox = []

    # staff user can add reviews. default category for reviews is editing.
    response_user_staff = self.client_staff.post('/api/review/', {
      'story': self.story_A.pk,
      'assignee': self.user_A.pk
    })
    self.assertEqual(response_user_staff.status_code, 200)
    self.assertEqual(response_user_staff.json()['category'], Review.EDITING)

    # check the review we've just created. Both `assigned_by` and `due_date` should be present. 
    review = Review.objects.get(pk=response_user_staff.json()['id'])
    self.assertEqual(review.assignee.username, self.user_A.username)
    self.assertEqual(review.assigned_by.username, self.user_staff.username)
    self.assertEqual(review.status, Review.INITIAL)
    self.assertTrue(review.due_date is not None)

    # reviewer (review.assignee) should have received an email
    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(mail.outbox[0].to, [self.user_A.email])

    # When we create a Review, `story.status` value changes according to the review category.
    self.story_A.refresh_from_db()
    self.assertEqual(self.story_A.status, Story.EDITING)

    # A normal user cannot access `under reviews` stories. This raises a NOT FOUND ERROR
    response_user_B = self.client_user_B.get('/api/story/%s/' % self.story_A.slug)
    self.assertEqual(response_user_B.status_code, 404)

    # ... while chiefreviewers can.
    response_user_D = self.client_user_D.get('/api/story/%s/' % self.story_A.slug)
    self.assertEqual(response_user_D.status_code, 200)
    self.assertEqual(response_user_D.json()['status'], Story.EDITING)

    # ... while assignee can.
    response_user_A = self.client_user_A.get('/api/story/%s/' % self.story_A.slug)
    self.assertEqual(response_user_A.status_code, 200)
    self.assertEqual(response_user_A.json()['status'], Story.EDITING)

    # A normal user cannot complete a review (NOT FOUND)
    # ... while assignee can.
    # response_user_A = self.client_user_A.patch('/api/review/%s/' % review.pk, {
    #   'status': Review.BOUNCE
    # })
    # print response_user_A.json()

    # self.assertEqual(response_user_A.status_code, 200)


  #def _test_create_editing_review(self):

  def test_suite(self):
    self._test_chief_reviewer_can_access_story()
    self._test_create_editing_review()
    self.cleanUp()