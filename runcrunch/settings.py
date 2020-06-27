"""
Django settings for runcrunch project.

Generated by 'django-admin startproject' using Django 3.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import dj_database_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['localhost', 'runcrunch.herokuapp.com', 'www.run-crunch.com']

# Application definition

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'activity_dashboard',
    'home.apps.Login',
    'webhook',
    'payment',

    'django_plotly_dash.apps.DjangoPlotlyDashConfig',
    'channels',
    'channels_redis',
    'django_tables2',
    'crispy_forms',
    'django_social_share',

    'django.contrib.admin',
    'django.contrib.auth',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.strava'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'django_plotly_dash.middleware.BaseMiddleware',
    'django_plotly_dash.middleware.ExternalRedirectionMiddleware',
]

ROOT_URLCONF = 'runcrunch.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ os.path.join(BASE_DIR, 'templates') ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "django.template.context_processors.request"
            ],
        },
    },
]

WSGI_APPLICATION = 'runcrunch.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=False)
        }

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',

    'allauth.account.auth_backends.AuthenticationBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ['GOOGLE_CLIENT_ID'],
            'secret': os.environ['GOOGLE_CLIENT_SECRET']
        }
    },
    'strava': {
        'APP': {
            'client_id': os.environ['STRAVA_CLIENT_ID'],
            'secret': os.environ['STRAVA_CLIENT_SECRET']
        }
    },
}

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

CRISPY_TEMPLATE_PACK = 'bootstrap4'

ASGI_APPLICATION = 'runcrunch.routing.applications'

CHANNEL_LAYERS = {
        'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                        'hosts': [('127.0.0.1', 6379), ('www.run-crunch.com', 6379)],
                        }
                }
            }

STATICFILES_FINDERS =  [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'django_plotly_dash.finders.DashAssetFinder',
        'django_plotly_dash.finders.DashComponentFinder',
        'django_plotly_dash.finders.DashAppDirectoryFinder'
        ]

PLOTLY_COMPONENTS = [
        'dash_core_components',
        'dash_html_components',

        'dash_renderer',
        'dpd_components',
        'dash_table',
        'dash_bootstrap_components'
        ]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

#STATICFILES_LOCATION = 'static'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'runcrunch/static'),
         ("js", os.path.join(STATIC_ROOT, 'js')),
         ("css", os.path.join(STATIC_ROOT, 'css')),
         ("img", os.path.join(STATIC_ROOT, 'img')),
         ("fonts", os.path.join(STATIC_ROOT, 'fonts')),
         ("vendor", os.path.join(STATIC_ROOT, 'vendor')),
         ("scss", os.path.join(STATIC_ROOT, 'scss')),
        ]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

LOGIN_REDIRECT_URL = '/dashboard'

LOGIN_URL = '/login'

LOGOUT_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = (
 'django.contrib.auth.backends.ModelBackend',
 )

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

SITE_ID = 4

CRISPY_CLASS_CONVERTERS = {
    'radioselect': "custom-control-input"
}

STRIPE_PUBLISHABLE_KEY = 'pk_live_z1sPeJjQcW88Z2yLfYtjhlr0000Zj1LTM5'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False
COMPRESS_STORAGE = "compressor.storage.GzipCompressorFileStorage"
COMPRESS_ROOT = os.path.abspath(STATIC_ROOT)
COMPRESS_ENABLED =  True
COMPRESS_PRECOMPILERS = (
    ("text/x-sass", "django_libsass.SassCompiler"),
    ("text/x-scss", "django_libsass.SassCompiler"),
)
COMPRESS_FILTERS = {
    "css": [
        "compressor.filters.css_default.CssAbsoluteFilter",
        "compressor.filters.cssmin.rCSSMinFilter",
    ],
    "js": ["compressor.filters.jsmin.JSMinFilter"],
}

# SMPT CONFIG
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'runcrunch.contact@gmail.com'
EMAIL_HOST_PASSWORD = os.environ['GMAIL_PW']

# Logging
DEBUG_PROPAGATE_EXCEPTIONS = True