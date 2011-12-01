#!/usr/bin/env python
import time

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

wds = []
pats = []

for i in range(4,10):
    pf = open("/var/www/xw/wl/%d.pat" % i)
    pdict = {}
    for patstr in pf:
        (pat, freq) = patstr.split(": ")
        pdict[pat] = int(freq)
    pf.close()
    pats.append(pdict)

for i in range(3,16):
    wf = open("/var/www/xw/wl/%d" % i)
    wdict = {}
    for wordstr in wf:
        wd = ""
        for j in range(len(wordstr)):
            wd += tt[ord(wordstr[j:j+1])]
        wdict[wd] = wordstr.strip()
    wf.close()
    wds.append(wdict)

def words(pat):
    list = []
    try:
        length = len(pat)
        for wd in wds[length - 3].keys():
            m = True
            for i in range(length):
                if not pat[i:i+1] == '.' and not pat[i:i+1] == wd[i:i+1]:
                    m = False
                    break
            if m:
                list.append(wd)
    except:
        pass
    return list

def patcount(pat):
    count = 0.00001
    patindex = len(pat) - 4
    if patindex >= 0 and patindex < 6:
        try:
            if pats[patindex].has_key(pat):
                count = pats[patindex][pat]
        except:
            pass
    return count

    
    
