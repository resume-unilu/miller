#!/usr/bin/env python
# -*- coding: utf-8 -*-
MILLER_TITLE = 'MILLER'
MILLER_DESCRIPTION = 'Your miller http meta description.'
MILLER_DEBUG = False


# """
# AUTH & DJANGO_SOCIAL_AUTH
# Put different parameters here according to the AUTHENTICATION_BACKENDS used.
# """
SECRET_KEY = 'YOUR SUPER SECRET KEY'

AUTHENTICATION_BACKENDS = (
  # 'social.backends.google.GoogleOAuth2',
  # 'social.backends.twitter.TwitterOAuth',
  'django.contrib.auth.backends.ModelBackend',
)

# SOCIAL_AUTH_TWITTER_KEY = ''
# SOCIAL_AUTH_TWITTER_SECRET = ''


# SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'XXXYYYZZ.apps.googleusercontent.com'
# SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

# SOCIAL_AUTH_FACEBOOK_APPID = 'XXXXXXXX' # insert here your facebook APPID

# """
# DJANGO_SEO for hosted prerender.io
# more information at https://github.com/skoczen/django-seo-js
# """
# SEO_JS_BACKEND = "django_seo_js.backends.PrerenderHosted"
# SEO_JS_PRERENDER_URL = "http://my-prerenderapp.com/"  # Note trailing slash.
# SEO_JS_PRERENDER_RECACHE_URL = "http://my-prerenderapp.com/recache"


"""
Zotero. Not yet used :(
"""
ZOTERO_API_KEY = 'XXX'
ZOTERO_IDENTITY = '123123123' #'user id numeric', ''
ZOTERO_BIB_FILE = 'zotero.bib'
ZOTERO_IDENTITY_NAME = 'your.zotero.username'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'USERNAME',
        'USER': 'DBNAME',
        'PASSWORD': 'PASSWORD'
    }
}

MILLER_OEMBEDS = {
  'EMBEDLY_API_KEY': 'xxx'
}

STATIC_ROOT = '/var/www/miller/dist'

# modify settings here
MILLER_WS_HOST = None

MILLER_SETTINGS = {
  'wshost': MILLER_WS_HOST,
  'host': 'https://yourwebsite.miller',
  'debug': MILLER_DEBUG,
  'disqus': '',
  'socialtags': 'resume-unilu', # socila tags when sharing on twitter
  'analytics': 'UA-XXXXXXX-1',
  'copyright': '',
  'copyrighturl': '',
}



# e.g modify with your smtp info
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'test@gmail.com'
EMAIL_HOST_PASSWORD = 'test'
EMAIL_PORT = 587
EMAIL_ACTIVATION_ACCOUNT = "info@miller.miller"


REGISTRATION_SALT = 'your registration salt'

# """
# RSS feed
# """
RSS_TITLE = 'RSS Miller - an rss feed'
RSS_DESCRIPTION = '''
  here below the rss description
'''


# """
# GOOGLE identification for SEO
# """
# Feel free to uncomment this ;)
GOOGLE_IDENTIFICATION = 'googleXxYyZz.html'
