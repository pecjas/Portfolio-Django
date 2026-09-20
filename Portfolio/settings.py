import os
import importlib.util

SETTINGS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SETTINGS_DIRECTORY) #Base is directory above settings.py

spec = importlib.util.spec_from_file_location("env", os.path.join(BASE_DIR, "env.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
env = module.get_env_settings()

SECRET_KEY = env.secret_key
GOOGLE_RECAPTCHA_SECRET_KEY = env.google_recaptcha_secret_key
GOOGLE_RECAPTCHA_SITE_KEY = env.google_recaptcha_site_key

GOOGLE_ANALYTICS_HEAD_INFO = env.google_analytics_head_info

# Rendered in the footer when set. Left blank until the profile URL is to hand.
LINKEDIN_URL = "https://www.linkedin.com/in/jason-j-peck/"

DEBUG = env.debug
ALLOWED_HOSTS = env.allowed_hosts

if not DEBUG:
    # PythonAnywhere terminates TLS at its proxy and forwards the original
    # scheme in this header. Without it, SECURE_SSL_REDIRECT sees every request
    # as plain HTTP and redirects forever.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Deliberately one hour, not a year. A misconfiguration here is remembered
    # by every visitor's browser for the full duration and cannot be called
    # back, so this starts short. Raise it to 31536000 once HTTPS has been
    # confirmed working in production for a while.
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

# Email setup
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env.email_host
EMAIL_USE_TLS = True
EMAIL_PORT = env.email_port
EMAIL_HOST_USER = env.email_host_user
EMAIL_HOST_PASSWORD = env.email_host_password

MEDIA_ROOT = env.media_root
MEDIA_URL = '/media/'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main.apps.MainConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # ConditionalGet adds the ETag that makes revalidation cheap; the one after
    # it asks browsers to revalidate HTML at all. Without the pair, a visitor
    # keeps the previous deploy's page and never requests the new stylesheet.
    'django.middleware.http.ConditionalGetMiddleware',
    'main.middleware.HtmlRevalidationMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Portfolio.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'main.context_processors.google_analytics_head_info',
                'main.context_processors.site_links'
            ],
        },
    },
]

WSGI_APPLICATION = 'Portfolio.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'

STATIC_ROOT = f'{BASE_DIR}/static'
