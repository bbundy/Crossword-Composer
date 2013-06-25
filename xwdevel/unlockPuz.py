#! /usr/bin/env python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))
import puz

print "unlocking %s" % sys.argv[1]
p = puz.read(sys.argv[1])
if p.locksum == 0:
    print "puzzle already unlocked"
    sys.exit(0)

locked = []
for i in range(p.width):
    for j in range(p.height):
        pos = p.width * j + i
        char = p.answers[pos:pos+1]
        if not char == '.':
            locked.append(char)
locked_str = ''.join(locked)

counter = 0

key = 1637
while counter < 10000:
    keystr = "%04d" % key
    digits = [int(keystr[0:1]),int(keystr[1:2]),int(keystr[2:3]),int(keystr[3:4])]
    unl = puz.unscramble(locked_str, digits)
    if puz.data_cksum(unl) == p.locksum and counter > 430:
        print "counter: %d" % counter
        break
    key += 163
    key = key % 10000
    counter += 1

print "key is %s" % keystr

p.locksum = 0

answers = []
counter = 0
for i in range(p.height):
    for j in range(p.width):
        pos = p.width * j + i
        char = p.answers[pos:pos+1]
        if not char == '.':
            answers.append(unl[counter:counter+1])
            counter += 1
        else:
            answers.append('.')
# transpose
tanswers = []
for i in range(p.height):
    for j in range(p.width):
        tanswers.append(answers[j*p.width + i])

p.answers = ''.join(tanswers)

for i in range(p.height):
    print p.answers[i*p.width:i*p.width+p.width]

print
p.save(sys.argv[2])
