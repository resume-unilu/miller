import json
from actstream.models import any_stream
from django.core import mail
from django.conf import settings
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


  def _test_close_review(self):
    """
    Our CHIEF_REVIEWER is responible for CLOSING a review.
    conditions:
    
    1. The story reviewed should be in status=Story.REVIEW
    2. The CHIEF_REVIEWER shouldn't be implied (author or owner)
    """
    # Empty the test outbox
    mail.outbox = []

    # Chief reviewer user_D creates a Review for user_B.
    response_user_D = self.client_user_D.post('/api/review/', {
      'story': self.story_A.pk,
      'assignee': self.user_B.pk,
      'category': Review.DOUBLE_BLIND
    })
    self.assertEqual(response_user_D.status_code, 200)
    response_user_D_json = response_user_D.json()
    self.assertEqual(response_user_D_json['category'], Review.DOUBLE_BLIND)

    review = Review.objects.get(pk=response_user_D_json['id'])

    self.assertEqual(review.assignee.username, self.user_B.username)
    self.assertEqual(review.assigned_by.username, self.user_D.username)
    self.assertEqual(review.status, Review.INITIAL)
    self.assertEqual(review.story.title, self.story_A.title)
    self.assertEqual(review.story.status, Story.REVIEW)

    # check the mail
    self.assertEqual(len(mail.outbox), 2)
    self.assertEqual(u''.join(mail.outbox[0].to), self.user_B.email)
    
    # Empty the test outbox
    mail.outbox = []
    
    # user B finishes the review, cannot make PATCH for some reason.
    # But it should send the emails correctly.
    review.contents = 'Very good, it is perfect. The paper just misses the title and the text.'
    review.status   = review.APPROVED
    review.originality_score = 2
    review.save()

    self.assertEqual(len(mail.outbox), 3)
    print '////////////////////////'
    print 'primo:'
    print mail.outbox[0].to
    print mail.outbox[0].subject
    print '------------------------'
    print mail.outbox[0].body
    print '////////////////////////'
    self.assertEqual(u''.join(mail.outbox[0].to), self.user_B.email)
    
    print 'secondo:'
    print mail.outbox[1].to
    print mail.outbox[1].subject
    print '------------------------'
    print mail.outbox[1].body
    print '////////////////////////'
    self.assertEqual(u''.join(mail.outbox[1].to), self.user_D.email)
    
    print 'terzo:'
    print mail.outbox[2].to
    print mail.outbox[2].subject
    print '------------------------'
    print mail.outbox[2].body
    print '////////////////////////'
    self.assertEqual(u''.join(mail.outbox[2].to), settings.DEFAULT_FROM_EMAIL)
    
    # Empty the test outbox
    mail.outbox = []
    
    # Now chief reviewer canc lose the review. A bad request:
    response_user_D = self.client_user_D.post('/api/review/close/', {
      #'story': self.story_A.pk,
      'status': Review.REFUSAL
    })
    self.assertEqual(response_user_D.status_code, 400)
    
    # Then the good one
    response_user_D=self.client_user_D.post('/api/review/close/', {
      'story': self.story_A.pk,
      'status': Review.REFUSAL,
      'contents': json.dumps({
        'title': 'Very nice story',
        'text': 'please consider for publication'
      })
    })
    self.assertEqual(response_user_D.status_code, 200)
    self.assertEqual(response_user_D.json()['category'], Review.CLOSING_REMARKS)

    review = Review.objects.get(pk=response_user_D.json()['id'])
    
    self.assertEqual(review.assignee.username, self.user_D.username)
    self.assertEqual(review.assigned_by.username, self.user_D.username)
    self.assertEqual(review.status, Review.REFUSAL)
    self.assertEqual(review.story.status, Story.REVIEW_DONE)

    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(u''.join(mail.outbox[0].to), settings.DEFAULT_FROM_EMAIL)
    self.assertEqual(mail.outbox[0].subject, '%s - review completed for manuscript "%s"' % (settings.MILLER_TITLE,review.story.title,))
    
    print 'ON Story.REVIEWDONE'
    print mail.outbox[0].to
    print mail.outbox[0].subject
    print '------------------------'
    print mail.outbox[0].body
    print '////////////////////////'



  def test_suite(self):
    self._test_chief_reviewer_can_access_story()
    self._test_create_editing_review()
    self._test_close_review()
    self.cleanUp()