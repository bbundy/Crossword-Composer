#! /usr/bin/env python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))
from importPUZ import impPUZ
from time import sleep

files = [
'mgwcc190.puz',
]
for f in files:
    print "http://67.207.128.158/xw/upload/%s" % f
    try:
        impPUZ("http://67.207.128.158/xw/upload/%s" % f,"MGWCC")
    except Exception:
        print "failed"

