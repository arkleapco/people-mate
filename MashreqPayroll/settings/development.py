import os
from MashreqPayroll.settings.base import *


DEBUG = True
# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # 'NAME': 'people_mate_shoura',
        # 'NAME': 'test_shoura',
        'NAME': 'XX_DEV_DB',
        'USER': 'mashreq_sysadmin',
        'PASSWORD': 'M@$hreq123',
        # 'HOST': 'localhost',
        'HOST': '159.223.119.143',
        'PORT': '',
    }
}








