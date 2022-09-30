from .psw import dbase_psw

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'blog',
        'USER': 'portaluser',
        'PASSWORD': dbase_psw,
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
