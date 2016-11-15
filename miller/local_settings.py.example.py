MILLER_TITLE = 'MILLER'
MILLER_DEBUG = False

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

MILLER_SETTINGS = {
  'debug': MILLER_DEBUG,
  'disqus': 'xxx'   
}

# e.g modify with your smtp info
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'test@gmail.com'
EMAIL_HOST_PASSWORD = 'test'
EMAIL_PORT = 587
EMAIL_ACTIVATION_ACCOUNT = "info@miller.miller"


REGISTRATION_SALT = 'your registration salt'