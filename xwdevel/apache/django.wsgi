import os
import sys

path = '/home/bbundy/sites'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'xw.settings'
os.environ['PYTHON_EGG_CACHE'] = '/tmp/egg-cache/'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
