"""miller URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap

from rest_framework import routers

from miller import views, api
from miller.feeds import LatestEntriesFeed, AtomLatestEntriesFeed
from miller.views import _share
#from miller.forms import SignupForm
# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter(trailing_slash=True)

router.register(r'user', api.UserViewSet)
router.register(r'collection', api.CollectionViewSet)
router.register(r'story', api.StoryViewSet)
router.register(r'caption', api.CaptionViewSet)
router.register(r'document', api.DocumentViewSet)
router.register(r'mention', api.MentionViewSet)
router.register(r'profile', api.ProfileViewSet)
router.register(r'tag', api.TagViewSet)
router.register(r'comment', api.CommentViewSet)
router.register(r'author', api.AuthorViewSet)
router.register(r'pulse', api.PulseViewSet)

from django.contrib.auth import views as auth_views
#from registration.views import RegistrationView

urlpatterns = [
  url(r'^$', views.home, name='home'),
  url(r'^admin/', admin.site.urls),
  url(r'^sitemap\.xml$', sitemap, name='sitemap-xml'),
  url(r'^api/', include(router.urls)),
  url(r'^api-auth/', include('rest_framework.urls')),

  url(r'^login/$', auth_views.login, {'template_name': 'login.html'}, name='login_view'), # views.login_view, name='login_view'),
  # url(r'^login/$', views.login_view, name='login_view'),
  
  url(r'^signup/$', views.signup_view, name='signup_view'),


  url(r'^logout/$', views.logout_view, name='logout_view'),
  url(r'^social/', include('social.apps.django_app.urls', namespace='social')),
  
  url(r'^latest/rss\.xml$', LatestEntriesFeed(), name='latest_rss'),
  url(r'^latest/atom/$', AtomLatestEntriesFeed()),

  url(r'^auth/', include('djoser.urls.authtoken')),
  url(r'^captcha/', include('captcha.urls')),
  url(r'^accounts/activate/complete/', views.activation_complete, name='activation_complete'),
  url(r'^accounts/', include('registration.backends.hmac.urls')),

  url(r'^', include('templated_email.urls', namespace='templated_email')),

  
  # url(r'^(?!(login|logout)).*$', views.home, name='app'),
  url(r'^(?!favicon\.ico|signup|media).*$', views.home, name='app')
]


if settings.DEBUG:
  from django.conf.urls.static import static
  urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
  urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)