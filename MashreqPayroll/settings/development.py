import os
from MashreqPayroll.settings.base import *


DEBUG = True
# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'people_mate',
        'USER': 'mashreq_sysadmin',
        'PASSWORD': 'M@$hreq123',
        'HOST': '165.22.19.247',
        'PORT': '',
    }
}








