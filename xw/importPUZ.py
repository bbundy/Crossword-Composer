#! /usr/bin/env python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))
import xwcore
from urllib import urlopen
from xword.models import  Clue, User, UserType, PuzzleType, Grid, Puzzle
from datetime import date
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.encoding import smart_str

def impPUZ(url, publisher=None):
    puz_handle = urlopen(url)
    file_contents = puz_handle.read()

    p = xwcore.Puzzle.fromPUZ(file_contents)
    if publisher:
        p.publisher = publisher
    try:
        setter = User.objects.get(username=p.author)
    except Exception, e:
        setter = User(username=p.author, puzzle_pref=PuzzleType.objects.get(type='US'), user_type=UserType.objects.get(type='Setter'), joined=date.today())
        setter.save()

    try:
        publisher = User.objects.get(username=p.publisher)
    except Exception, e:
        publisher = User(username=p.publisher, puzzle_pref=PuzzleType.objects.get(type='US'), user_type=UserType.objects.get(type='Publisher'), joined=date.today())
        publisher.save()

    if hasattr(p, "editor"):
        try:
            editor = User.objects.get(username=p.editor)
        except Exception, e:
            editor = User(username=p.editor, puzzle_pref=PuzzleType.objects.get(type='US'), user_type=UserType.objects.get(type='Editor'), joined=date.today())
            editor.save()
    else:
        editor = setter

    if hasattr(p, "date"):
        (m, d, y) = p.date.split('/')
        pdate = date(int(y),int(m),int(d))
    else:
        pdate = date.today()
    if hasattr(p, "type"):
        try:
            ptype = PuzzleType.objects.get(type=p.type)
        except Exception:
            ptype = PuzzleType(type=p.type)
            ptype.save()
    else:
        ptype = PuzzleType.objects.get(type="US")

    try:
        grid = Grid.objects.get(format=p.dbgridstr)
    except Exception:
        grid = Grid(format=p.dbgridstr, type=ptype)
        grid.save()

    try:
        puzzle = Puzzle.objects.get(setter=setter, publisher=publisher, editor=editor, date=pdate, title=p.title, type=ptype)
        print "using existing puzzle"
    except Exception:
            puzzle = Puzzle(setter=setter, publisher=publisher, editor=editor, date=pdate, title=p.title, type=ptype, grid=grid) 
            try:
                puzzle.save()
            except Exception:
                t = ""
                for i in range(len(p.title)):
                    if ord(p.title[i:i+1]) < 0x80:
                        t += p.title[i:i+1]
                p.title=t
                puzzle = Puzzle(setter=setter, publisher=publisher, editor=editor, date=pdate, title=t, type=ptype, grid=grid) 
                puzzle.save()


    for clue in p.across:
        if clue.dir == "across":
            dir = 1
        else:
            dir = 2

        try:
            cl = Clue.objects.get(puzzle__title=p.title, num=clue.num, dir=dir)
            cl.answer=clue.ans
            cl.text=smart_str(clue.clue)
            cl.type=ptype
            cl.save()

        except ObjectDoesNotExist:
            cl = Clue(setter=setter, puzzle=puzzle, row=clue.row, col=clue.col, num=clue.num, answer=clue.ans, dir=dir, text=clue.clue, type=ptype)
            try:
                cl.save()
            except Exception:
                t = ""
                for i in range(len(clue.clue)):
                    if ord(clue.clue[i:i+1]) < 0x80:
                        t += clue.clue[i:i+1]
                cl.text = t
                cl.save()
        except MultipleObjectsReturned:
            print "multiple clues found for %s %s %s" % (clue.ans, clue.clue, p.title)
        except Exception:
            t = ""
            for i in range(len(clue.clue)):
                if ord(clue.clue[i:i+1]) < 0x80:
                    t += clue.clue[i:i+1]
            cl.text = t
            cl.save()

    for clue in p.down:
        if clue.dir == "across":
            dir = 1
        else:
            dir = 2

        try:
            cl = Clue.objects.get(puzzle__title=p.title, num=clue.num, dir=dir)
            cl.answer=clue.ans
            cl.text=smart_str(clue.clue)
            cl.type=ptype
            cl.save()
        except ObjectDoesNotExist:
            cl = Clue(setter=setter, puzzle=puzzle, row=clue.row, col=clue.col, num=clue.num, answer=clue.ans, dir=dir, text=clue.clue, type=ptype)
            try:
                cl.save()
            except Exception:
                t = ""
                for i in range(len(clue.clue)):
                    if ord(clue.clue[i:i+1]) < 0x80:
                        t += clue.clue[i:i+1]
                cl.text = t
                cl.save()
        except MultipleObjectsReturned:
            print "multiple clues found for %s %s %s" % (clue.ans, clue.clue, p.title)
        except Exception:
            t = ""
            for i in range(len(clue.clue)):
                if ord(clue.clue[i:i+1]) < 0x80:
                    t += clue.clue[i:i+1]
            cl.text = t
            cl.save()

