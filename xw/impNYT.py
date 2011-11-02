#! /usr/bin/env python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))
from datetime import date, timedelta
from time import sleep
from importXPF import impXPF

(m, d, y) = sys.argv[1].split('/')
fromdate = date(int(y),int(m),int(d))

(m, d, y) = sys.argv[2].split('/')
todate = date(int(y),int(m),int(d))

thisdate = fromdate

months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
while thisdate <= todate:
    month = months[thisdate.month - 1]
    url = thisdate.strftime("http://www.xwordinfo.com/xml/Puzzles/%%Y/%s%%d-%%Y.xml" % month)
    print "Importing: %s" % url
    try:
        impXPF(url)
    except IndexError:
        pass
    thisdate += timedelta(1)
    sleep(5)
