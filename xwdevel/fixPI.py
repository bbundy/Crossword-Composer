#! /usr/bin/env python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))
from xword.models import Grid, Puzzle, User

pipuzzles = Puzzle.objects.filter(publisher=1219)
for p in pipuzzles:
    oldformat = p.grid.format
    newformat = oldformat.replace("15u","15c")
    g = Grid.objects.filter(format=oldformat)
    if (len(g) == 1):
        print "replacing %s with %s" % (oldformat, newformat)
        g[0].format = newformat
        g[0].save()
