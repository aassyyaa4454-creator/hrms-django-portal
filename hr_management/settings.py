import os
from pathlib import Path
import dj_database_url # أضفنا هذه المكتبة

BASE_DIR = Path(__file__).resolve().parent.parent

# Render بيئة الانتاج في 
# إذا كنا على ريندر سيستخدم مفتاح حماية من ريندر، وإلا سيستخدم المفتاح العادي
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# سيكون False على الإنترنت لحماية الموقع، و True على جهازك
DEBUG = 'RENDER' not in os.environ

# السماح لريندر بتشغيل الموقع
ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hr_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # أضفنا هذه لقراءة ملفات CSS/JS على الانترنت
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hr_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'hr_app' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'hr_app.context_processors.user_profile',
            ],
        },
    },
]

WSGI_APPLICATION = 'hr_management.wsgi.application'

# إعدادات قاعدة البيانات الذكية
# إذا وجد رابط قاعدة بيانات من ريندر سيستخدمه (PostgreSQL)
# إذا لم يجد، سيستخدم إعدادات جهازك المحلي (MySQL)
DATABASES = {
    'default': dj_database_url.config(
        default=f"mysql://{os.environ.get('DB_USER', 'root')}:{os.environ.get('DB_PASSWORD', '')}@{os.environ.get('DB_HOST', 'localhost')}:{os.environ.get('DB_PORT', '3306')}/{os.environ.get('DB_NAME', 'hr_management_db')}",
        conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Aden'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'hr_app' / 'static']

# الإعدادات الجديدة الضرورية لرفع الملفات الثابتة على الانترنت
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
