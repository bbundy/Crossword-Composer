#! /usr/bin/env python
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))
import xwcore
from urllib import urlopen
from xword.models import  Clue, User, UserType, PuzzleType, Grid, Puzzle
from datetime import date
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

def impXPF(url):
    xml_handle = urlopen(url)
    fname = "-".join(sys.argv[1].split("/")) + ".xpf"
    file_contents = xml_handle.read()
    save_file = open("/home/bbundy/puzzles/nyt/" + fname,"w")
    save_file.write(file_contents)
    save_file.close()
    try:
        PuzzleType.objects.get(type="Cryptic")
    except ObjectDoesNotExist:
        t = PuzzleType(type="Cryptic")
        t.save()
        t = PuzzleType(type="US")
        t.save()

    try:
        UserType.objects.get(type="Setter")
    except ObjectDoesNotExist:
        t = UserType(type="Setter")
        t.save()
        t = UserType(type="Editor")
        t.save()
        t = UserType(type="Publisher")
        t.save()
        t = UserType(type="Solver")
        t.save()

    p = xwcore.Puzzle.fromXML(file_contents)

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

    try:
        editor = User.objects.get(username=p.editor)
    except Exception, e:
        editor = User(username=p.editor, puzzle_pref=PuzzleType.objects.get(type='US'), user_type=UserType.objects.get(type='Editor'), joined=date.today())
        editor.save()

    if p.date:
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
    elif p.publisher == "The New York Times":
        ptype = PuzzleType.objects.get(type="US")
    else:
        ptype = PuzzleType.objects.get(type="Cryptic")

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
        puzzle.save()

    for clue in p.across:
        if clue.dir == "across":
            dir = 1
        else:
            dir = 2

        try:
            cl = Clue.objects.get(puzzle__title=p.title, num=clue.num, dir=dir)
            cl.answer=clue.ans
            cl.text=clue.clue
            cl.type=ptype
            cl.save()
        except ObjectDoesNotExist:
            cl = Clue(setter=setter, puzzle=puzzle, row=clue.row, col=clue.col, num=clue.num, answer=clue.ans, dir=dir, text=clue.clue, type=ptype)
            cl.save()
        except MultipleObjectsReturned:
            print "multiple clues found for %s %s %s" % (clue.ans, clue.clue, p.title)

    for clue in p.down:
        if clue.dir == "across":
            dir = 1
        else:
            dir = 2

        try:
            cl = Clue.objects.get(puzzle__title=p.title, num=clue.num, dir=dir)
            cl.answer=clue.ans
            cl.text=clue.clue
            cl.type=ptype
            cl.save()
        except ObjectDoesNotExist:
            cl = Clue(setter=setter, puzzle=puzzle, row=clue.row, col=clue.col, num=clue.num, answer=clue.ans, dir=dir, text=clue.clue, type=ptype)
            cl.save()
        except MultipleObjectsReturned:
            print "multiple clues found for %s %s %s" % (clue.ans, clue.clue, p.title)

