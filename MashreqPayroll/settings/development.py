import os
from MashreqPayroll.settings.base import *


DEBUG = True
"""
# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
      }
  }

"""
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
<<<<<<< HEAD


=======
>>>>>>> 0986963a28703bf2727aaeef3b13c34f0ba325f6




