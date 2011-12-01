#!/usr/bin/env python
import sys, os
import time
from operator import itemgetter

wordfile = open(sys.argv[1])

tt = range(256)
for i in range(0x40):
    tt[i] = ''
for i in range(0x41,0x5B):
    tt[i] = '%s' %  chr(i + 0x20)
for i in range(0x5B,0x60):
    tt[i] = ''
for i in range(0x60,0x7B):
    tt[i] = '%s' % chr(i)
for i in range(0x7B,0x80):
    tt[i] = ''

for i in range(0x80,0xC0):
    tt[i] = ''

for i in range(0xC0,0xC7):
    tt[i] = 'a'
for i in range(0xC7,0xC8):
    tt[i] = 'c'
for i in range(0xC8,0xCC):
    tt[i] = 'e'
for i in range(0xCC,0xD0):
    tt[i] = 'i'
    
tt[208] = 'd'
tt[209] = 'n'
 
for i in range(0xD2,0xD9):
    tt[i] = 'o'
for i in range(0xD9,0xDD):
    tt[i] = 'u'
for i in range(0xDD,0xE0):
    tt[i] = 'y'
for i in range(0xE0,0xE7):
    tt[i] = 'a'
for i in range(0xE7,0xE8):
    tt[i] = 'c'
for i in range(0xE8,0xEC):
    tt[i] = 'e'
for i in range(0xEC,0xF0):
    tt[i] = 'i'

tt[240] = 'd'
tt[241] = 'n'

for i in range(0xF2,0xF9):
    tt[i] = 'o'
for i in range(0xF9,0xFD):
    tt[i] = 'u'
for i in range(0xFD,0xFF):
    tt[i] = 'y'

class pat:
    def __init__(self, pat):
        self.pat = pat

pats = {}
wd_to_disp = {}
cutoffs = [2,2,2,2,2,2,5,10,10,10,10,5,5,5,5,5,5,5]

for wordstr in wordfile:
    wd = ""
    for i in range(len(wordstr)):
        wd += tt[ord(wordstr[i:i+1])]
    wd_to_disp[wd] = wordstr.strip()
    length = len(wd)
    for i in range(2**length):
        pat = ""
        for place in range(length):
            if ((2**place) & i) == 0:
                pat += wd[place:place+1]
            else:
                pat += '.'
        if pats.has_key(pat):
            pats[pat] += 1
        else:
            pats[pat] = 1

spats = sorted(pats.iteritems(), key=itemgetter(1), reverse=True)

for k, v in spats:
    if v > cutoffs[len(k)]:
        print "%s: %d" % (k, v)

# numcts = {}
# for k,v in spats:
#    if numcts.has_key(v):
#        numcts[v] += 1
#    else:
#        numcts[v] = 1

#for k,v in numcts.iteritems():
#    print "count %d has %d matches" % (k,v)

wordfile.close()
