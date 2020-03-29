import os
import environ

SETTINGS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SETTINGS_DIRECTORY) #Base is directory above settings.py

env = environ.Env(
    ALLOWED_HOSTS=(list, ['127.0.0.1:8000']),
    DEBUG=(bool, False),
    EMAIL_HOST=str,
    EMAIL_HOST_PASSWORD=str,
    EMAIL_HOST_USER=str,
    EMAIL_PORT=int,
    GOOGLE_RECAPTCHA_SECRET_KEY=str,
    GOOGLE_RECAPTCHA_SITE_KEY=str,
    MEDIA_ROOT=str,
    SECRET_KEY=str,
)

env_file = os.path.join(BASE_DIR, '.env')
print(env_file)
print(os.getpid())
environ.Env.read_env(env_file)

SECRET_KEY = env('SECRET_KEY')
GOOGLE_RECAPTCHA_SECRET_KEY = env('GOOGLE_RECAPTCHA_SECRET_KEY')
GOOGLE_RECAPTCHA_SITE_KEY = env('GOOGLE_RECAPTCHA_SITE_KEY')

DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Email setup
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_USE_TLS = True
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

MEDIA_ROOT = env('MEDIA_ROOT')
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

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

STATIC_ROOT = f'{BASE_DIR}/static'
