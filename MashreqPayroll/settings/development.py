import os
from MashreqPayroll.settings.base import *


DEBUG = True
# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'XX_BKUP_SHOURA',
        'USER': 'mashreq_sysadmin',
        'PASSWORD': 'M@$hreq123',
        'HOST': 'localhost',
        #'HOST': '159.223.119.143',
        'PORT': '',
    }
}








