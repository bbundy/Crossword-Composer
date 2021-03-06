import xml.parsers.expat
import urllib
import puz
import re
from django.utils.encoding import smart_unicode
from xword.models import Answer
#from pyx import *
#text.set(mode="latex")
#text.preamble(r"\usepackage{times}")
#text.size(-4)

class Clue:
    def __init__(self, attrs, data, rebus, grid_only = False):
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
        length = self.length
        for i in range(self.length):
            rb = None
            if i > length:
                break
            if self.dir == 'across':
                if rebus and rebus.has_key("%d-%d" % (self.row, self.col + i)):
                    rb = rebus["%d-%d" % (self.row, self.col + i)]
                    self.ans = self.ans.replace(rb.data, rb.short)
                    self.sq.append((i+1, rb.data.lower(), 'style=font-size:0.7em'))
                    length -= len(rb.data)
                    continue
            if self.dir == 'down':
                if rebus and rebus.has_key("%d-%d" % (self.row + i, self.col)):
                    rb = rebus["%d-%d" % (self.row + i, self.col)]
                    self.ans = self.ans.replace(rb.data, rb.short)
                    self.sq.append((i+1, rb.data.lower(), 'style=font-size:0.7em'))
                    length -= len(rb.data)
                    continue
            if rb == None:
                if self.ans[i:i+1] == '?' or self.ans[i:i+1] == ' ' or grid_only:
                    self.sq.append((i+1, "", ""))
                else:
                    self.sq.append((i+1, self.ans[i:i+1].lower(), ""))
        self.cr = 7 + 35 * (int(self.row) - 1)
        self.cc = 7 + 35 * (int(self.col) - 1)
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

class Rebus:
    def __init__(self, attrs, data):
        self.row = int(attrs["Row"])
        self.col = int(attrs["Col"])
        self.short = attrs["Short"]
        self.data = data

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
            self.clue.append(Clue(self.attrs, self.data, self.rebus, self.grid_only))
            self.attrs = {}
        if self.element == "Rebus":
            self.rebus["%s-%s" % (self.attrs["Row"], self.attrs["Col"])] = Rebus(self.attrs, self.data)
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
        if self.element == "Rows":
            self.height = int(self.data)
        if self.element == "Cols":
            self.width = int(self.data)
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
        this.rebus = {}
        this.grid_only = grid_only
        p = xml.parsers.expat.ParserCreate(encoding="utf-8")
        p.StartElementHandler = this.start_element
        p.EndElementHandler = this.end_element
        p.CharacterDataHandler = this.char_data
        p.Parse(puzzle_xml)
        this.size = len(this.row)
        this.setGrid()
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
                    if clue.col - 1 + i < this.width:
                        this.format[clue.row - 1][clue.col - 1 + i].setVal(0)
                if (clue.col - 1 + i < this.width) and not grid_only and not clue.ans[i:i+1] == '?' and not grid_only:
                    this.format[clue.row - 1][clue.col - 1 + i].setLetter(clue.ans[i:i+1])
            for down in this.down:
                if (down.col >= clue.col) and (down.col < clue.col + clue.length) and (clue.row >= down.row) and (clue.row < down.row + down.length):
                    this.across_intersections["%d-across-%d" % (clue.num, down.col - clue.col + 1)] = "%d-down-%d" % (down.num, clue.row - down.row + 1)

        for clue in this.down:
            for i in range(clue.length):
                if i == 0:
                    this.format[clue.row - 1][clue.col - 1].setVal(clue.num)
                else:
                    if clue.row - 1 + i < this.height:
                        this.format[clue.row - 1 + i][clue.col - 1].setVal(0)
                if (clue.row - 1 + i < this.height) and not grid_only and not clue.ans[i:i+1] == '?' and not grid_only:
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

        for clue in this.clue:
            i = clue.row - 1
            j = clue.col - 1
            pos = 1
            shortans = ''
            while True:
                if i >= this.height or j >= this.width:
                    break
                let = this.row[i][j:j+1].lower()
                if let == ".":
                    break
                shortans += let
                if clue.dir == 'across':
                    j += 1
                else:
                    i += 1
            if len(shortans) < len(clue.ans):
                clue.fullans = clue.ans
                clue.ans = shortans
                clue.sq = []
                for i in range(len(shortans)):
                    clue.sq.append((i+1, shortans[i:i+1], None))
        this.getStats()
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
        this.height = this.size
        this.format = []
        this.clue = []
        this.across = []
        this.down = []
        this.rebus={}
        this.intersections = []
        this.down_intersections = {}
        this.across_intersections = {}
        rnum = 0
        for r in rows:
            cols = r.split('x')
            cols.pop()
            this.width = len(cols)
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
                                clue = Clue(attrs, cl, None)
                                this.across.append(clue)
                            if post.has_key("%s-down-input" % c):
                                cl = post["%s-down-input" % c]
                                dir = "down"
                                attrs["Dir"] = dir
                                clue = Clue(attrs, cl, None)
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
                if (clue.col - 2 + i) < this.width:
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
                if (clue.row - 2 + i) < this.width:
                    this.format[clue.row - 2 + i][clue.col - 1].isletter = True
                    this.format[clue.row - 2 + i][clue.col - 1].letter = letter
                ans += letter
                i += 1
            clue.ans = ans.upper()
            clue.length = len(ans)
        this.row = []
        for i in range(this.height):
            this.row.append([])
            this.row[i] = ""
            for j in range(this.width):
                if this.format[i][j].isletter:
                    letter = this.format[i][j].letter
                else:
                    letter = '.'
                this.row[i] += letter

        for clue in this.across:
            this.clue.append(clue)
            for down in this.down:
                if (down.col >= clue.col) and (down.col < clue.col + clue.length) and (clue.row >= down.row) and (clue.row < down.row + down.length):
                    this.across_intersections["%d-across-%d" % (clue.num, down.col - clue.col + 1)] = "%d-down-%d" % (down.num, clue.row - down.row + 1)

        for clue in this.down:
            this.clue.append(clue)
            for across in this.across:
                if (across.row >= clue.row) and (across.row < clue.row + clue.length) and (clue.col >= across.col) and (clue.col < across.col + across.length):
                    this.down_intersections["%d-down-%d" % (clue.num, across.row - clue.row + 1)] = "%d-across-%d" % (across.num, clue.col - across.col + 1)

        for k in sorted(this.across_intersections.keys()):
            this.intersections.append((k,this.across_intersections[k]))

        for k in sorted(this.down_intersections.keys()):
            this.intersections.append((k,this.down_intersections[k]))

        this.getStats()
        return this

    def setGrid(self):
        self.format = []
        gridstrs = []
        gridstr = ""
        gridlen = 0
        for r in range(self.height):
            self.format.append([])
            for s in range(self.width):
                if self.row[r][s:s+1] == '.':
                    self.format[r].append(Square(-1))
                    gridstr += "."
                else:
                    self.format[r].append(Square(0))
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
        self.dbgridstr = "%d" % self.width
        if self.width == self.height:
            if hasattr(self, "type"):
                if self.type.lower() == "cryptic":
                    self.dbgridstr += "c"
                else:
                    self.dbgridstr += "u"
        else:
            self.dbgridstr += "x%02d" % self.height
        for gs in gridstrs:
            self.dbgridstr += gridlookup[gs]

    @classmethod
    def fromGrid(cls, gridstr):
        this = cls()
        this.dbgridstr = gridstr
        this.size = int(gridstr[0:2])
        this.height = this.size
        this.width = this.size
        startpat = 3
        if gridstr[2:3] == 'u':
            this.type = "us"
        elif gridstr[2:3] == 'c':
            this.type = "cryptic"
        elif gridstr[2:3] == 'x':
            this.type = 'us'
            this.width = this.size
            this.height = int(gridstr[3:5])
            this.size = this.height
            startpat = 5
        formatstr=""
        this.row=[]
        for chr in gridstr[startpat:]:
            formatstr += gridreverse[chr]
        for i in range(this.height):
            this.row.append(formatstr[i*this.width:i*this.width+this.width])

        this = Puzzle.getFromRows(this)
        this.getStats()
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
    def fromPUZ(cls, pz):
        this = cls()
        this.author = pz.author
        this.title = pz.title
        this.publisher = pz.copyright
        this.size = max(pz.width, pz.height)
        this.height = pz.height
        this.width = pz.width
        this.row=[]
        for i in range(this.height):
            this.row.append(pz.answers[i*this.width:i*this.width+this.width])
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
        this.setGrid()
        this.getStats()
        return this

    def toPUZ(self):
        pz = puz.Puzzle()
        pz.width = self.width
        pz.height = self.height
        pz.author = self.author
        pz.title = self.title
        answers = []
        fill = []
        for i in range(self.height):
            answers.append(self.row[i].upper().encode('latin-1'))
        pz.answers= ''.join(answers)
        for i in range(self.height):
            fillrow=[]
            for j in range(self.width):
                if self.row[i][j:j+1] == '.':
                    fillrow.append('.')
                else:
                    fillrow.append('-')
            fill.append(''.join(fillrow))
        pz.fill = ''.join(fill).encode('latin-1')
        pz.clues=[]
        across = 0
        down = 0
        while True:
            if across + down > len(self.clue):
                break;
            if across < len(self.across):
                across_clue = self.across[across]
            else:
                across_clue = None
            if down < len(self.down):
                down_clue = self.down[down]
            else:
                down_clue = None
            if down_clue:
                if across_clue == None or down_clue.num < across_clue.num:
                    pz.clues.append(down_clue.clue)
                    down += 1
                    continue
            if across_clue:
                pz.clues.append(across_clue.clue)
                across += 1
                continue
            break
        return pz

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
        this.height = len(this.row)
        this.width = len(blocks[0])
        this = Puzzle.getFromRows(this)
        this.getStats()
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
        for i in range(1, this.height+1):
            this.format.append([])
            for j in range(1, this.width+1):
                if this.row[i-1][j-1:j] == '.':
                    this.format[i-1].append(Square(-1))
                else:
                    this.format[i-1].append(Square(0))
                    if j == 1 or this.row[i-1][j-2:j-1] == '.':  # beginning of horizontal clue
                        if j - 1 < this.width - 2 and this.row[i-1][j:j+1] != '.':  #room for a word
                            clue_len = 2
                            cl = this.row[i-1][j-1:j+1]
                            while j + clue_len - 1 < this.width and this.row[i-1][j+clue_len-1:j+clue_len] != '.':
                                cl += this.row[i-1][j+clue_len-1:j+clue_len]
                                clue_len += 1
                            attrs = {}
                            attrs["Num"] = clue_num
                            attrs["Row"] = i
                            attrs["Col"] = j
                            attrs["Ans"] = cl
                            attrs["Dir"] = "across"
                            this.across.append(Clue(attrs,"", None))
                            this.clue.append(Clue(attrs,"", None))
                            this.format[i-1][j-1].setVal(clue_num)

                    if i == 1 or this.row[i-2][j-1:j] == '.':  # beginning of vertical clue
                        if i - 1 < this.height - 2 and this.row[i][j-1:j] != '.':  #room for a word
                            clue_len = 2
                            cl = this.row[i-1][j-1:j] + this.row[i][j-1:j]
                            while i + clue_len -1 < this.height and this.row[i+clue_len-1][j-1:j] != '.':
                                cl += this.row[i+clue_len-1][j-1:j]
                                clue_len += 1
                            attrs = {}
                            attrs["Num"] = clue_num
                            attrs["Row"] = i
                            attrs["Col"] = j
                            attrs["Ans"] = cl
                            attrs["Dir"] = "down"
                            this.down.append(Clue(attrs,"", None))
                            this.clue.append(Clue(attrs,"", None))
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

    def initial_stack(self):
        stack = []
        for cl in self.clue:
            if cl.ans.find('?') == -1:
                stack.append('%d-%s&%s' % (cl.num, cl.dir, cl.ans))
        return stack

    def fill_clue(self, stack):
        best = None
        bestscore = 0.0
        bestnum = 1000
        filled = {}
        for s in stack:
            vals = s.split('&')
            filled[vals[0]] = vals[1]
            
        for cl in self.clue:
            if filled.has_key("%d-%s" % (cl.num, cl.dir)):
                continue
            letcount = 0
            clen = len(cl.ans)
            for i in range(clen):
                if not cl.ans[i:i+1] == '?':
                    letcount += 1
            if letcount > 0:
                ct = Answer.objects.extra(where=['answer LIKE "%s"' % cl.ans.replace('?','_')]).count()
                if ct == 0:
                    return cl
                score = 100.0/ct
                if score == bestscore and cl.num < bestnum:
                    best = cl
                    bestnum = cl.num
                if score > bestscore:
                    bestscore = score
                    bestnum = cl.num
                    best = cl
        return best

    def filled_count(self, clue):
        count = 0
        for i in range(clue.length):
            if not clue.ans[i:i+1] == '?':
                count += 1
        return count

    def cross_hash(self, clue):
        if clue.dir == "across":
            ret = self.across_intersections
        else:
            ret = self.down_intersections
        return ret

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
                    xing[xing_clue.col - clue.col] = (int(pos), xing_clue.length, xing_clue.ans, n1 + "-" + ad)
        else:
            for inter in self.down_intersections.keys():
                if re.match(clue_str + ".*", inter):
                    (n1,ad,pos) = self.down_intersections[inter].split('-')
                    xing_clue = self.clue_from_str(n1, ad)
                    xing[xing_clue.row - clue.row] = (int(pos), xing_clue.length, xing_clue.ans, n1 + "-" + ad)
        return xing

    def getStats(self):
        wd_cts = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        let_cts = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.block_ct = 0
        self.let_ct = 0
        self.wd_ct = 0
        self.ave_wdlen = 0.0
        self.scr = 0

        for c in self.clue:
            wd_cts[c.length-3] += 1
            self.wd_ct += 1
            self.ave_wdlen += c.length

        for r in self.row:
            for i in range(len(r)):
                let = r[i:i+1]
                if let == '.':
                    self.block_ct += 1
                else:
                    self.let_ct += 1
                    n = ord(let.upper())
                    if n >= ord('A') and n <= ord('Z'):
                        let_cts[n - ord('A')] += 1
                        self.scr += scrabble[n - ord('A')]

        self.ave_wdlen /= self.wd_ct
        self.ave_wdlen = "%2.2f" % self.ave_wdlen
        self.ave_scr = "%2.2f" % (float(self.scr)/float(self.let_ct))

        self.a_ct = let_cts[0]
        self.b_ct = let_cts[1]
        self.c_ct = let_cts[2]
        self.d_ct = let_cts[3]
        self.e_ct = let_cts[4]
        self.f_ct = let_cts[5]
        self.g_ct = let_cts[6]
        self.h_ct = let_cts[7]
        self.i_ct = let_cts[8]
        self.j_ct = let_cts[9]
        self.k_ct = let_cts[10]
        self.l_ct = let_cts[11]
        self.m_ct = let_cts[12]
        self.n_ct = let_cts[13]
        self.o_ct = let_cts[14]
        self.p_ct = let_cts[15]
        self.q_ct = let_cts[16]
        self.r_ct = let_cts[17]
        self.s_ct = let_cts[18]
        self.t_ct = let_cts[19]
        self.u_ct = let_cts[20]
        self.v_ct = let_cts[21]
        self.w_ct = let_cts[22]
        self.x_ct = let_cts[23]
        self.y_ct = let_cts[24]
        self.z_ct = let_cts[25]

        self.ct_3 = wd_cts[0]
        self.ct_4 = wd_cts[1]
        self.ct_5 = wd_cts[2]
        self.ct_6 = wd_cts[3]
        self.ct_7 = wd_cts[4]
        self.ct_8 = wd_cts[5]
        self.ct_9 = wd_cts[6]
        self.ct_10 = wd_cts[7]
        self.ct_11 = wd_cts[8]
        self.ct_12 = wd_cts[9]
        self.ct_13 = wd_cts[10]
        self.ct_14 = wd_cts[11]
        self.ct_15 = wd_cts[12]
        self.ct_16 = wd_cts[13]
        self.ct_17 = wd_cts[14]
        self.ct_18 = wd_cts[15]
        self.ct_19 = wd_cts[16]
        self.ct_20 = wd_cts[17]
        self.ct_21 = wd_cts[18]
        self.ct_22 = wd_cts[19]
        self.ct_23 = wd_cts[20]
        self.ct_24 = wd_cts[21]

scrabble = [1, 3, 3, 2, 1, 4, 2, 4, 1, 8, 5, 1, 3, 1, 1, 3, 10, 1, 1, 1, 1, 4, 4, 8, 4, 10]
#    def savePDF(self):
#        c = canvas.canvas()
#        squares = []
#        for i in range(self.height):
#            for j in range(self.width):
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
