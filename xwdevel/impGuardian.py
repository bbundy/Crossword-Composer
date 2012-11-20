#! /usr/bin/env python
import sys, os
import simplejson
from datetime import date
from django.utils.encoding import smart_unicode
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
os.environ['DJANGO_SETTINGS_MODULE'] = 'xwdevel.settings'
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))
import xwcore
from xword.models import  Clue, User, UserType, PuzzleType, Grid, Puzzle, Answer

across_answers={}
down_answers={}

across_clues={}
down_clues={}

across_pos={}
down_pos={}

last_num = None
words_for_clue={}
answers={}

months = { "January": 1, "February" : 2, "March": 3, "April": 4, "May": 5, "June": 6, "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12 }

def save_clue(clue, p, setter, editor, publisher, puzzle, ptype):
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
        try:
            ans = Answer.objects.get(answer=cl.answer)
        except ObjectDoesNotExist:
            ans = Answer(answer=cl.answer, count=1)
            ans.save()
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
        try:
            ans = Answer.objects.get(answer=cl.answer)
            ans.count += 1
            ans.save()
        except ObjectDoesNotExist:
            ans = Answer(answer=cl.answer, count=1)
            ans.save()

    except MultipleObjectsReturned:
        print "multiple clues found for %s %s %s" % (clue.ans, clue.clue, p.title)
    except Exception:
        t = ""
        for i in range(len(clue.clue)):
            if ord(clue.clue[i:i+1]) < 0x80:
                t += clue.clue[i:i+1]
        cl.text = t
        cl.save()

with open(sys.argv[1]) as f:
    for line in f:
        if line.find("words_for_clue[\"") >=0:
            exec line.strip()
        if line.find("solutions[\"") >=0:
            parts = line.split("\"")
            apts = parts[1].split('-')
            num = int(apts[0])
            if apts[1] == "across":
                if across_answers.has_key(num):
                    across_answers[num] += parts[3]
                else:
                    across_answers[num] = parts[3]
            elif apts[1] == "down":
                if down_answers.has_key(num):
                    down_answers[num] += parts[3]
                else:
                    down_answers[num] = parts[3]

        if line.find("class=\"across\"") > 0 and line.find("div id=") > 0:
            x = int(line.split("left: ")[1].split('px')[0])/29
            y = int(line.split("top: ")[1].split('px')[0])/29
            num = int(line.split("\"")[1].split("-")[0])
            across_pos[num] = (x, y)

        if line.find("class=\"down\"") > 0 and line.find("div id=") > 0:
            x = int(line.split("left: ")[1].split('px')[0])/29
            y = int(line.split("top: ")[1].split('px')[0])/29
            num = int(line.split("\"")[1].split("-")[0])
            down_pos[num] = (x, y)

        if line.find("-across-clue") > 0:
            last_num  = int(line.split("\"")[1].split("-")[0])
            clue_dict = across_clues

        if line.find("-down-clue") > 0:
            last_num  = int(line.split("\"")[1].split("-")[0])
            clue_dict = down_clues

        if line.find("</label></li>") > 0:
            clue_dict[last_num] = smart_unicode(line.split("</label>")[0].strip()).replace(u"\u2014","-")

        if line.find("<li class=\"byline\">") > 0:
            author = line.split(">")[2].split("<")[0]

        if line.find("<li class=\"publication\">") > 0:
            d = line.split(',')[1].strip().split(" ")
            day = int(d[1])
            month = months[d[2]]
            year = int(d[3])

    for num in across_answers.keys():
        answers["%d-across" % num] = across_answers[num]

    for num in down_answers.keys():
        answers["%d-down" % num] = down_answers[num]

    num = sys.argv[1].split('/')[-1]
    title = "Guardian %s" % num
    p = xwcore.Puzzle.fromDicts(author, title, across_answers, down_answers, across_pos, down_pos, across_clues, down_clues)
    pz = p.toPUZ()
    s = pz.tostring()
    pf = open("/var/www/xw/upload/%s.puz" % num, "w")
    pf.write(s)
    pf.close()
    p.publisher = "Guardian"

    try:
        setter = User.objects.get(username=p.author)
    except Exception, e:
        setter = User(username=p.author, puzzle_pref=PuzzleType.objects.get(type='Cryptic'), user_type=UserType.objects.get(type='Setter'), joined=date.today())
        setter.save()

    try:
        publisher = User.objects.get(username=p.publisher)
    except Exception, e:
        publisher = User(username=p.publisher, puzzle_pref=PuzzleType.objects.get(type='Cryptic'), user_type=UserType.objects.get(type='Publisher'), joined=date.today())
        publisher.save()

    editor = setter

    pdate = date(int(year),int(month),int(day))
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
        save_clue(clue, p, setter, editor, publisher, puzzle, ptype)

    for clue in p.down:
        save_clue(clue, p, setter, editor, publisher, puzzle, ptype)

