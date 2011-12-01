import xml.parsers.expat
import urllib
import puz
import re
from django.utils.encoding import smart_unicode
#from pyx import *
#text.set(mode="latex")
#text.preamble(r"\usepackage{times}")
#text.size(-4)

class Clue:
    def __init__(self, attrs, data, grid_only = False):
        self.row = int(attrs["Row"])
        self.col = int(attrs["Col"])
        self.num = int(attrs["Num"])
        self.dir = attrs["Dir"].lower()
        self.ans = attrs["Ans"]
        if data == ".":
            data = "(%d)" % len(self.ans) 
        if grid_only:
            self.clue = ""
        else:
            self.clue = data
        self.length = len(self.ans)
        self.sq = []
        for i in range(self.length):
            if self.ans[i:i+1] == '?' or self.ans[i:i+1] == ' ' or grid_only:
                self.sq.append((i+1, ""))
            else:
                self.sq.append((i+1, self.ans[i:i+1].lower()))
        self.cr = 11 + 35 * (int(self.row) - 1)
        self.cc = 11 + 35 * (int(self.col) - 1)
        self.is_across = (self.dir == "across")

class Square:
    def __init__(self,val):
        self.block = False
        self.space = False
        self.num = False
        self.isletter = False
        if val < 0:
            self.block = True
        if val == 0:
            self.space = True
        if val > 0:
            self.num = True
            self.val = val

    def setVal(self,val):
        if not self.num:
            self.block = False
            if val > 0:
                self.space = False
                self.num = True
                self.val = val
            else:
                self.space = True

    def setLetter(self,val):
        self.isletter = True
        self.letter = val[0:1].lower()

# <Puzzles Version="1.0">
#   <Puzzle>
#     <Type>cryptic</Type>
#     <Title>NY Times, Sun, Oct 02, 2011 CRYPTIC CROSSWORD</Title>
#     <Author>Emily Cox and Henry Rathvon</Author>
#     <Editor>Will Shortz</Editor>
#     <Publisher>The New York Times</Publisher>
#     <Date>10/2/2011</Date>
#     <Size>
#       <Rows>15</Rows>
#       <Cols>15</Cols>
#     </Size>
#     <Grid>
#       <Row>RAGA.REARWINDOW</Row>
#       <Row>E.E...L.O.N.A.A</Row>
#     </Grid>
#     <Clues>
#       <Clue Row="1" Col="1" Num="1" Dir="Across" Ans="RAGA">Piece by Joplin and a piece by Shankar (4)</Clue>
#       <Clue Row="1" Col="6" Num="3" Dir="Across" Ans="REARWINDOW">Opening in a building both narrow and wide, strangely (4,6)</Clue>
#       <Clue Row="3" Col="1" Num="9" Dir="Across" Ans="SORE">Angry fly is heard (4)</Clue>
#       <Clue Row="3" Col="6" Num="10" Dir="Across" Ans="BARBECUING">Behind tavern, be giving the signal by grilling (10)</Clue>
#       <Clue Row="5" Col="1" Num="12" Dir="Across" Ans="PHILANDERING">Philip &amp; Erin Green carrying on a flirtation (10)</Clue>

class Puzzle:
    def start_element(self, name, attrs):
        self.element = name
        self.attrs = attrs
        self.data = ""

    def end_element(self, name):
        if self.element == "Row":
            self.row.append(self.data)
        if self.element == "Clue":
            self.clue.append(Clue(self.attrs, self.data, self.grid_only))
            self.attrs = {}
        if self.element == "Title":
            self.title = self.data
        if self.element == "Author":
            self.author = self.data
            if len(self.author) > 30:
                self.author = self.author[:30]
        if self.element == "Editor":
            self.editor = self.data
        if self.element == "Publisher":
            self.publisher = self.data
        if self.element == "Date":
            self.date = self.data
        if self.element == "Type":
            self.type = self.data
        self.element = ""
        self.attrs = {}

    def char_data(self, data):
        self.data += data

    def __init__(self):
        pass

    @classmethod
    def fromXML(cls, puzzle_xml, grid_only = False):
        global gridlookup
        this = cls()
        this.element = ""
        this.row = []
        this.clue = []
        this.grid_only = grid_only
        p = xml.parsers.expat.ParserCreate(encoding="utf-8")
        p.StartElementHandler = this.start_element
        p.EndElementHandler = this.end_element
        p.CharacterDataHandler = this.char_data
        p.Parse(puzzle_xml)
        this.size = len(this.row)
        this.format = []
        gridstrs = []
        gridstr = ""
        gridlen = 0
        for r in range(this.size):
            this.format.append([])
            for s in range(this.size):
                if this.row[r][s:s+1] == '.':
                    this.format[r].append(Square(-1))
                    gridstr += "."
                else:
                    this.format[r].append(Square(0))
                    gridstr += "?"
                gridlen += 1
                if gridlen % 6 == 0:
                    gridstrs.append(gridstr)
                    gridstr = ""
        while not (gridlen % 6 == 0):
            gridstr += '?'
            gridlen += 1
        if len(gridstr) == 6:
            gridstrs.append(gridstr)
        this.dbgridstr = "%d" % this.size
        if hasattr(this, "type"):
            if this.type.lower() == "cryptic":
                this.dbgridstr += "c"
        else:
            this.dbgridstr += "u"
        for gs in gridstrs:
            this.dbgridstr += gridlookup[gs]
        this.across = []
        this.down = []
        this.across_intersections = {}
        this.down_intersections = {}
        this.intersections = []
        if grid_only:
            this.title = "NewCrossword"
            this.author = "Anonymous"
        for clue in this.clue:
            if clue.dir == "across":
                this.across.append(clue)
            if clue.dir == "down":
                this.down.append(clue)
        for clue in this.across:
            for i in range(clue.length):
                if i == 0:
                    this.format[clue.row - 1][clue.col - 1].setVal(clue.num)
                else:
                    if clue.col - 1 + i < this.size:
                        this.format[clue.row - 1][clue.col - 1 + i].setVal(0)
                if (clue.col - 1 + i < this.size) and not grid_only and not clue.ans[i:i+1] == '?' and not grid_only:
                    this.format[clue.row - 1][clue.col - 1 + i].setLetter(clue.ans[i:i+1])
            for down in this.down:
                if (down.col >= clue.col) and (down.col < clue.col + clue.length) and (clue.row >= down.row) and (clue.row < down.row + down.length):
                    this.across_intersections["%d-across-%d" % (clue.num, down.col - clue.col + 1)] = "%d-down-%d" % (down.num, clue.row - down.row + 1)

        for clue in this.down:
            for i in range(clue.length):
                if i == 0:
                    this.format[clue.row - 1][clue.col - 1].setVal(clue.num)
                else:
                    if clue.row - 1 + i < this.size:
                        this.format[clue.row - 1 + i][clue.col - 1].setVal(0)
                if (clue.row - 1 + i < this.size) and not grid_only and not clue.ans[i:i+1] == '?' and not grid_only:
                    this.format[clue.row - 1 + i][clue.col - 1].setLetter(clue.ans[i:i+1])
            for across in this.across:
                if (across.row >= clue.row) and (across.row < clue.row + clue.length) and (clue.col >= across.col) and (clue.col < across.col + across.length):
                    this.down_intersections["%d-down-%d" % (clue.num, across.row - clue.row + 1)] = "%d-across-%d" % (across.num, clue.col - across.col + 1)

        for k in sorted(this.across_intersections.keys()):
            this.intersections.append((k,this.across_intersections[k]))

        for k in sorted(this.down_intersections.keys()):
            this.intersections.append((k,this.down_intersections[k]))
        
        this.formatstr = ""
        for row in this.format:
            for sq in row:
                if sq.block:
                    this.formatstr += "bx"
                elif sq.space:
                    this.formatstr += "sx"
                elif sq.num:
                    this.formatstr += "%dx" % sq.val
            this.formatstr += "e"
                
        return this

    @classmethod
    def fromPOST(cls, post):
        this = cls()
        rows = post['format'].split('e')
        rows.pop()
        if post.has_key('title'):
            this.title = post['title']
        if post.has_key('author'):
            this.author = post['author']
        this.type = 'cryptic'
        if post.has_key('gridstr'):
            if post['gridstr'][2:3] == 'u':
                this.type = 'us'
            this.dbgridstr = post['gridstr']
        this.size = len(rows)
        this.format = []
        this.across = []
        this.down = []
        this.intersections = []
        this.down_intersections = {}
        this.across_intersections = {}
        rnum = 0
        for r in rows:
            cols = r.split('x')
            cols.pop()
            if rnum < this.size:
                this.format.append([])
                cnum = 0
                for c in cols:
                    if cnum < this.size:
                        if c == 's':
                            this.format[rnum].append(Square(0))
                        elif c == 'b':
                            this.format[rnum].append(Square(-1))
                        else:
                            try:
                                this.format[rnum].append(Square(int(c)))
                            except ValueError:
                                this.format[rnum].append(Square(0))
                            attrs = {}
                            attrs["Num"] = c
                            attrs["Row"] = str(rnum + 1)
                            attrs["Col"] = str(cnum + 1)
                            attrs["Ans"] = ""
                            if post.has_key("%s-across-input" % c):
                                cl = post["%s-across-input" % c]
                                dir = "across"
                                attrs["Dir"] = dir
                                clue = Clue(attrs, cl)
                                this.across.append(clue)
                            if post.has_key("%s-down-input" % c):
                                cl = post["%s-down-input" % c]
                                dir = "down"
                                attrs["Dir"] = dir
                                clue = Clue(attrs, cl)
                                this.down.append(clue)
                    cnum += 1
            rnum += 1

        for clue in this.across:
            ans = ""
            i = 1
            while True:
                if post.has_key("%d-across-%d" % (clue.num, i)):
                    c = post["%d-across-%d" % (clue.num, i)]
                    if len(c) == 0 or c == ' ':
                        letter = "?"
                    else: 
                        letter = c[0:1].lower()
                else:
                    break
                if (clue.col - 2 + i) < this.size:
                    this.format[clue.row - 1][clue.col - 2 + i].isletter = True
                    this.format[clue.row - 1][clue.col - 2 + i].letter = letter
                ans += letter
                i += 1
            clue.ans = ans.upper()
            clue.length = len(ans)
                
        for clue in this.down:
            ans = ""
            i = 1
            while True:
                if post.has_key("%d-down-%d" % (clue.num, i)):
                    c = post["%d-down-%d" % (clue.num, i)]
                    if len(c) == 0 or c == ' ':
                        letter = "?"
                    else: 
                        letter = c[0:1].lower()
                else:
                    break
                if (clue.row - 2 + i) < this.size:
                    this.format[clue.row - 2 + i][clue.col - 1].isletter = True
                    this.format[clue.row - 2 + i][clue.col - 1].letter = letter
                ans += letter
                i += 1
            clue.ans = ans.upper()
            clue.length = len(ans)
        this.row = []
        for i in range(this.size):
            this.row.append([])
            this.row[i] = ""
            for j in range(this.size):
                if this.format[i][j].isletter:
                    letter = this.format[i][j].letter
                else:
                    letter = '.'
                this.row[i] += letter

        for clue in this.across:
            for down in this.down:
                if (down.col >= clue.col) and (down.col < clue.col + clue.length) and (clue.row >= down.row) and (clue.row < down.row + down.length):
                    this.across_intersections["%d-across-%d" % (clue.num, down.col - clue.col + 1)] = "%d-down-%d" % (down.num, clue.row - down.row + 1)

        for clue in this.down:
            for across in this.across:
                if (across.row >= clue.row) and (across.row < clue.row + clue.length) and (clue.col >= across.col) and (clue.col < across.col + across.length):
                    this.down_intersections["%d-down-%d" % (clue.num, across.row - clue.row + 1)] = "%d-across-%d" % (across.num, clue.col - across.col + 1)

        for k in sorted(this.across_intersections.keys()):
            this.intersections.append((k,this.across_intersections[k]))

        for k in sorted(this.down_intersections.keys()):
            this.intersections.append((k,this.down_intersections[k]))

        return this

    @classmethod
    def fromGrid(cls, gridstr):
        this = cls()
        this.dbgridstr = gridstr
        this.size = int(gridstr[0:2])
        if gridstr[2:3] == 'u':
            this.type = "us"
        else:
            this.type = "cryptic"

        formatstr=""
        this.row=[]
        for chr in gridstr[3:]:
            formatstr += gridreverse[chr]
        for i in range(this.size):
            this.row.append(formatstr[i*this.size:i*this.size+this.size])

        this = Puzzle.getFromRows(this)
                
        return this

    @classmethod
    def fromCookie(cls, cookie):
        this = cls()
        uc = urllib.unquote(cookie)
        pairs=uc.split('&')
        for pair in pairs:
            s = pair.split('=')
            if s[0] == 'gridstr':
                return Puzzle.fromGrid(s[1])
        return None

    @classmethod
    def fromPUZ(cls, puz_file):
        this = cls()
        pz = puz.load(puz_file)
        this.author = pz.author
        this.title = pz.title
        this.publisher = pz.copyright
        this.size = pz.width
        this.row=[]
        for i in range(this.size):
            this.row.append(pz.answers[i*this.size:i*this.size+this.size])
        this = Puzzle.getFromRows(this)
        for i in range(len(pz.clues)):
            this.clue[i].clue = pz.clues[i]
        this.across = []
        this.down = []
        for clue in this.clue:
            if clue.dir == "across":
                this.across.append(clue)
            if clue.dir == "down":
                this.down.append(clue)
        return this

    @classmethod
    def fromGridPOST(cls, post):
        this = cls()
        this.size = 15
        this.row=[]
        blocks=[]
        for i in range(this.size):
            blocks.append([])
            for j in range(this.size):
                blocks[i].append('?')
        for k,v in post.items():
            if v == 'x':
                m = re.match("col-(\d+)-(\d+)", k)
                r = int(m.group(1))
                c = int(m.group(2))
                blocks[r-1][c-1] = '.'
        for r in range(this.size):
            this.row.append("")
            for c in blocks[r]:
                this.row[r] += c
        this = Puzzle.getFromRows(this)
        return this

    def getFromRows(this):
        this.format = []
        this.across = []
        this.down = []
        this.clue = []
        this.across_intersections = {}
        this.down_intersections = {}
        this.intersections = []
        clue_num = 1
        for i in range(1, this.size+1):
            this.format.append([])
            for j in range(1, this.size+1):
                if this.row[i-1][j-1:j] == '.':
                    this.format[i-1].append(Square(-1))
                else:
                    this.format[i-1].append(Square(0))
                    if j == 1 or this.row[i-1][j-2:j-1] == '.':  # beginning of horizontal clue
                        if j - 1 < this.size - 2 and this.row[i-1][j:j+1] != '.':  #room for a word
                            clue_len = 2
                            cl = this.row[i-1][j-1:j+1]
                            while j + clue_len - 1 < this.size and this.row[i-1][j+clue_len-1:j+clue_len] != '.':
                                cl += this.row[i-1][j+clue_len-1:j+clue_len]
                                clue_len += 1
                            attrs = {}
                            attrs["Num"] = clue_num
                            attrs["Row"] = i
                            attrs["Col"] = j
                            attrs["Ans"] = cl
                            attrs["Dir"] = "across"
                            this.across.append(Clue(attrs,""))
                            this.clue.append(Clue(attrs,""))
                            this.format[i-1][j-1].setVal(clue_num)

                    if i == 1 or this.row[i-2][j-1:j] == '.':  # beginning of vertical clue
                        if i - 1 < this.size - 2 and this.row[i][j-1:j] != '.':  #room for a word
                            clue_len = 2
                            cl = this.row[i-1][j-1:j] + this.row[i][j-1:j]
                            while i + clue_len -1 < this.size and this.row[i+clue_len-1][j-1:j] != '.':
                                cl += this.row[i+clue_len-1][j-1:j]
                                clue_len += 1
                            attrs = {}
                            attrs["Num"] = clue_num
                            attrs["Row"] = i
                            attrs["Col"] = j
                            attrs["Ans"] = cl
                            attrs["Dir"] = "down"
                            this.down.append(Clue(attrs,""))
                            this.clue.append(Clue(attrs,""))
                            this.format[i-1][j-1].setVal(clue_num)
                if this.format[i-1][j-1].num:
                    clue_num += 1

        for clue in this.across:
            for down in this.down:
                if (down.col >= clue.col) and (down.col < clue.col + clue.length) and (clue.row >= down.row) and (clue.row < down.row + down.length):
                    this.across_intersections["%d-across-%d" % (clue.num, down.col - clue.col + 1)] = "%d-down-%d" % (down.num, clue.row - down.row + 1)

        for clue in this.down:
            for across in this.across:
                if (across.row >= clue.row) and (across.row < clue.row + clue.length) and (clue.col >= across.col) and (clue.col < across.col + across.length):
                    this.down_intersections["%d-down-%d" % (clue.num, across.row - clue.row + 1)] = "%d-across-%d" % (across.num, clue.col - across.col + 1)

        for k in sorted(this.across_intersections.keys()):
            this.intersections.append((k,this.across_intersections[k]))

        for k in sorted(this.down_intersections.keys()):
            this.intersections.append((k,this.down_intersections[k]))

        this.formatstr = ""
        for row in this.format:
            for sq in row:
                if sq.block:
                    this.formatstr += "bx"
                elif sq.space:
                    this.formatstr += "sx"
                elif sq.num:
                    this.formatstr += "%dx" % sq.val
            this.formatstr += "e"
        return this

    def clue_from_str(self, n1, ad):
        clue = None
        if ad == "across":
            for cl in self.across:
                if int(n1) == cl.num:
                    clue = cl
                    break
        else:
            for cl in self.down:
                if int(n1) == cl.num:
                    clue = cl
                    break
        return clue

    def filled_count(self, clue):
        count = 0
        for i in range(clue.length):
            if not clue.ans[i:i+1] == '?':
                count += 1
        return count

    def clue_xings(self, clue):
        xing = []
        for i in range(clue.length):
            xing.append(None)
        ad = clue.dir
        clue_str = "%d-%s" % (clue.num, ad)
        if ad == 'across':
            for inter in self.across_intersections.keys():
                if re.match(clue_str + ".*", inter):
                    (n1,ad,pos) = self.across_intersections[inter].split('-')
                    xing_clue = self.clue_from_str(n1, ad)
                    xing[xing_clue.col - clue.col] = (int(pos), xing_clue.length, xing_clue.ans)
        else:
            for inter in self.down_intersections.keys():
                if re.match(clue_str + ".*", inter):
                    (n1,ad,pos) = self.down_intersections[inter].split('-')
                    xing_clue = self.clue_from_str(n1, ad)
                    xing[xing_clue.row - clue.row] = (int(pos), xing_clue.length, xing_clue.ans)
        return xing

#    def savePDF(self):
#        c = canvas.canvas()
#        squares = []
#        size = self.size
#        for i in range(size):
#            for j in range(size):
#                rect = path.path(path.moveto(i, -j), path.lineto(i+1, -j),
#                                 path.lineto(i+1, -j-1), path.lineto(i, -j-1),
#                                 path.lineto(i, -j), path.closepath())
#                squares.append(rect)
#        sqnum = 0
#        for r in squares:
#            if sqnum % 7 == 0:
#                c.stroke(r, [deco.filled([color.grey(0.5)])])
#            else:
#                c.stroke(r, [style.linewidth.THIN])
#            c.text(sqnum/15 + 0.05, -(sqnum % 15) - 0.05, str(sqnum),  [text.halign.boxleft, text.valign.top])
#            sqnum += 1
#        c.writePDFfile("cw")


gridlookup = {}
gridlookup["??????"] = "A"
gridlookup["?????."] = "B"
gridlookup["????.?"] = "C"
gridlookup["????.."] = "D"
gridlookup["???.??"] = "E"
gridlookup["???.?."] = "F"
gridlookup["???..?"] = "G"
gridlookup["???..."] = "H"
gridlookup["??.???"] = "I"
gridlookup["??.??."] = "J"
gridlookup["??.?.?"] = "K"
gridlookup["??.?.."] = "L"
gridlookup["??..??"] = "M"
gridlookup["??..?."] = "N"
gridlookup["??...?"] = "O"
gridlookup["??...."] = "P"
gridlookup["?.????"] = "Q"
gridlookup["?.???."] = "R"
gridlookup["?.??.?"] = "S"
gridlookup["?.??.."] = "T"
gridlookup["?.?.??"] = "U"
gridlookup["?.?.?."] = "V"
gridlookup["?.?..?"] = "W"
gridlookup["?.?..."] = "X"
gridlookup["?..???"] = "Y"
gridlookup["?..??."] = "Z"
gridlookup["?..?.?"] = "a"
gridlookup["?..?.."] = "b"
gridlookup["?...??"] = "c"
gridlookup["?...?."] = "d"
gridlookup["?....?"] = "e"
gridlookup["?....."] = "f"
gridlookup[".?????"] = "g"
gridlookup[".????."] = "h"
gridlookup[".???.?"] = "i"
gridlookup[".???.."] = "j"
gridlookup[".??.??"] = "k"
gridlookup[".??.?."] = "l"
gridlookup[".??..?"] = "m"
gridlookup[".??..."] = "n"
gridlookup[".?.???"] = "o"
gridlookup[".?.??."] = "p"
gridlookup[".?.?.?"] = "q"
gridlookup[".?.?.."] = "r"
gridlookup[".?..??"] = "s"
gridlookup[".?..?."] = "t"
gridlookup[".?...?"] = "u"
gridlookup[".?...."] = "v"
gridlookup["..????"] = "w"
gridlookup["..???."] = "x"
gridlookup["..??.?"] = "y"
gridlookup["..??.."] = "z"
gridlookup["..?.??"] = "0"
gridlookup["..?.?."] = "1"
gridlookup["..?..?"] = "2"
gridlookup["..?..."] = "3"
gridlookup["...???"] = "4"
gridlookup["...??."] = "5"
gridlookup["...?.?"] = "6"
gridlookup["...?.."] = "7"
gridlookup["....??"] = "8"
gridlookup["....?."] = "9"
gridlookup[".....?"] = "_"
gridlookup["......"] = "."

gridreverse = dict((v,k) for k, v in gridlookup.iteritems())
