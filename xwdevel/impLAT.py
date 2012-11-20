#! /usr/bin/env python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))
from datetime import date, timedelta
from time import sleep
from importPUZ import impPUZ

(m, d, y) = sys.argv[1].split('/')
fromdate = date(int(y),int(m),int(d))

(m, d, y) = sys.argv[2].split('/')
todate = date(int(y),int(m),int(d))

thisdate = fromdate

while thisdate <= todate:
    url = thisdate.strftime("http://www.cruciverb.com/puzzles/lat/lat%y%m%d.puz")
    print "Importing: %s" % url
    try:
        data = impPUZ(url, "LA Times")
        f = open(thisdate.strftime("/home/bbundy/puzzles/lat/lat%y%m%d.puz"), 'w')
        f.write(data)
        f.close()
    except IndexError:
        pass
    thisdate += timedelta(1)
    sleep(5)
