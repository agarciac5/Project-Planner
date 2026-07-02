import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    ]


DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-development-only-change-me"
    else:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY es obligatoria cuando DJANGO_DEBUG=False."
        )

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1" if DEBUG else "",
)
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS es obligatoria cuando DJANGO_DEBUG=False."
    )

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "access_support",
    "academic_core",
    "teaching",
    "classrooms",
    "scheduling_enrollment",
]
AUTH_USER_MODEL = "access_support.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project_planner.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "access_support.context_processors.role_context",
            ],
        },
    },
]

WSGI_APPLICATION = "project_planner.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "0")),
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


# Endurecimiento de producción. El desarrollo local conserva HTTP.
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = int(
    os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000" if not DEBUG else "0")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# Limita cargas grandes, especialmente en la importación de estudiantes.
DATA_UPLOAD_MAX_MEMORY_SIZE = int(
    os.getenv("DJANGO_DATA_UPLOAD_MAX_MEMORY_SIZE", str(5 * 1024 * 1024))
)
FILE_UPLOAD_MAX_MEMORY_SIZE = int(
    os.getenv("DJANGO_FILE_UPLOAD_MAX_MEMORY_SIZE", str(5 * 1024 * 1024))
)

LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "900"))
IMPORT_MAX_ROWS = int(os.getenv("IMPORT_MAX_ROWS", "5000"))
SCHEDULE_MAX_COURSES = int(os.getenv("SCHEDULE_MAX_COURSES", "100"))
SCHEDULE_MAX_DEMAND = int(os.getenv("SCHEDULE_MAX_DEMAND", "10000"))
SCHEDULE_POPULATION_SIZE = int(os.getenv("SCHEDULE_POPULATION_SIZE", "80"))
SCHEDULE_GENERATIONS = int(os.getenv("SCHEDULE_GENERATIONS", "140"))
SCHEDULE_OPTIONS_LIMIT = int(os.getenv("SCHEDULE_OPTIONS_LIMIT", "3"))
