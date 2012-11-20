#! /usr/bin/env python
import sys, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'xwdevel.settings'
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))
from importPUZ import impPUZ
from time import sleep
url = sys.argv[1]
publisher = sys.argv[2]
fl = sys.argv[3]
data = impPUZ(url, publisher)
fh = open(fl,"w")
fh.write(data)
fh.close()

