from django.db import models

from miller.models import Story


class StoryHit(models.Model):
    VIEWED = 'viewed'
    DOWNLOADED = 'downloaded'

    action = models.CharField(max_length=24, choices=((VIEWED, VIEWED), (DOWNLOADED, DOWNLOADED)))
    story = models.ForeignKey(Story)
    hits = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.story)

    def increase(self):
        self.hits += 1
        self.save()


class HitCount(models.Model):
    story_hit = models.ForeignKey(StoryHit, editable=False, on_delete=models.CASCADE)
    ip = models.CharField(max_length=40)
    session = models.CharField(max_length=40)
    date = models.DateTimeField(auto_now=True)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def hit_count(request, story, action):
    if not request.session.session_key:
        request.session.save()
    s_key = request.session.session_key
    ip = get_client_ip(request)
    story_hit, story_hit_created = StoryHit.objects.get_or_create(story=story, action=action)

    if story_hit_created:
        hitcount, created = HitCount.objects.get_or_create(story_hit=story_hit, ip=ip, session=s_key)
        if created:
            story_hit.increase()
            request.session[ip] = ip
            request.session[request.path] = request.path
    else:
        if ip and request.path not in request.session:
            hitcount, created = HitCount.objects.get_or_create(story_hit=story_hit, ip=ip, session=s_key)
            if created:
                story_hit.increase()
                request.session[ip] = ip
                request.session[request.path] = request.path
    return story_hit.hits
