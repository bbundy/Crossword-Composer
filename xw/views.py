from __future__ import with_statement
from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django import forms
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_protect
from django.template import RequestContext
from subprocess import Popen, PIPE
from xwcore import Puzzle
from xword.models import Grid, RawPuzzles, SolvePuzzles
from random import randrange
from django.db.models import Q
import logging
import urllib
import re

class ContactForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea)
    email = forms.EmailField(max_length=40)

@csrf_protect
def member_request(request):
    if request.method == 'POST': # If the form has been submitted...
        form = ContactForm(request.POST) # A form bound to the POST data
        if form.is_valid():
            comment = form.cleaned_data['comment']
            email = form.cleaned_data['email']

            recipients = ['brbundy@gmail.com']

            send_mail("Crossword Composer Membership Request", comment, email, recipients)
            return HttpResponseRedirect('/thanks/')
    else:
        form = ContactForm() # An unbound form

    return render_to_response('contact.html', {
        'form': form,
    }, context_instance=RequestContext(request))

def thanks(request):
    t = get_template('thanks.html')
    html = t.render(Context({}))
    return HttpResponse(html)

def suggest_words(request):
    logger = logging.getLogger('xw.access')
    logger.info(" words  request from %s for %s" % (request.META['REMOTE_ADDR'], request.GET["pattern"]));
    pattern = request.GET["pattern"]
    length = len(pattern)
    pattern = pattern.replace('0','\\w[ \\-\',]*') + '.'
    words = open('/var/www/xw/wl/%d' % length)
    p1 = Popen(["grep", "^%s$" % pattern], stdin=words, stdout=PIPE)
    lines = 0
    resp = ''
    for line in p1.stdout:
        resp = resp + line.strip() + "&"
        if lines > 10:
            break

    resp = resp.rstrip('&')
    words.close()
    return HttpResponse(resp)

alph = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']

scores = [None,None,None]
for length in range(3,11):
    scores.append([])
    for pos in range(length):
        scores[length].append({})
        for let in alph:
            scores[length][pos][let] = 0

with open("/var/www/xw/wl/scores.txt") as sc:
    for line in sc:
        (length,pos,let,score) = line.split(',')
        length = int(length)
        pos = int(pos)
        score = int(score)
        scores[length][pos][let] = score

def score(word, xings):
    score = 1.0
    word = word.replace(" ","")
    word = word.replace("-","")
    word = word.replace("'","")
    word = word.replace(",","")
    word = word.lower()
    length = len(word)
    for i in range(length):
        if xings[i][1] <= 11:
            score = score * float(scores[xings[i][1]][xings[i][0] - 1][word[i:i+1]])
    return score
    
def ranked_words(request):
    logger = logging.getLogger('xw.access')
    logger.info(" ranked words  request from %s for %s" % (request.META['REMOTE_ADDR'], request.POST["active"]));
    resp = ''
    clue = request.POST['active'] 
    (n1,ad,pos) = clue.split('-')
    p = Puzzle.fromPOST(request.POST)
    active_clue = p.clue_from_str(n1, ad)
    if active_clue:
        word_matches = []
        xings = p.clue_xings(active_clue)
        pattern = active_clue.ans
        length = len(pattern)
        pattern = pattern.lower().replace('?','\\w[ \\-\',]*') + '.'
        words = open('/var/www/xw/wl/%d' % length)
        p1 = Popen(["grep", "^%s$" % pattern], stdin=words, stdout=PIPE)
        for line in p1.stdout:
            display_str = line.strip()
            sort_str = display_str.lower().replace(' ',"").replace("'","").replace("-","").replace(",","")
            word_matches.append((display_str, sort_str))
        words.close()
        word_matches.sort(lambda x,y: cmp(score(y[1],xings), score(x[1],xings)))
        resp = '&'.join(x[0] for x in word_matches)
    return HttpResponse(resp)

def main_landing(request):
    logger = logging.getLogger('xw.access')
    logger.info(" main page request from %s : %s" % (request.META['REMOTE_ADDR'], request.META['QUERY_STRING']));
    t = get_template('puzzle.html')
    p = None
    solver = None
    try:
        author = request.GET['author']
        title = request.GET['title']
        atname = author + "-" + title
        atname = atname.replace('/','_')
        atname = atname.replace('.','_')
        atname = atname.replace(' ','_')
        atname = atname.lower()
        table = RawPuzzles
        if request.GET.has_key('solve') or request.GET.has_key('solver'):
            t = get_template('solve.html')
            if request.GET.has_key('solver'):
                t = get_template('solver.html')
                solver = request.GET['solver']
                atname = solver + '-' + atname
                table = SolvePuzzles
        puz = table.objects.filter(author_title=atname)
        if len(puz) > 0:
            p = Puzzle.fromXML(puz[0].contents)
            if p.size > 18:
                t = get_template('puz21.html')
        if request.GET.has_key('print'):
            t = get_template('print.html') 
        if request.GET.has_key('printall'):
            t = get_template('printall.html') 
    except:
        pass

    if p == None: 
        gridstrs = Grid.objects.filter(Q(format__startswith='15u'))
        p = Puzzle.fromGrid(gridstrs[randrange(len(gridstrs))].format)
    if solver:
        p.solver = solver
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)

def gridedit(request):
    t = get_template('grid.html')
    try:
        p = Puzzle.fromPOST(request.POST)
    except:
        p = Puzzle.fromGrid("15uAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)

def usegrid(request):
    t = get_template('puzzle.html')
    p = Puzzle.fromGridPOST(request.POST)
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)

def print_cw(request):
    p = Puzzle.fromPOST(request.POST)
    if request.POST.has_key("printall"):
        return HttpResponseRedirect('/?%s' % urllib.urlencode((('author',p.author),('title',p.title),('printall','true'))))
    else:
        return HttpResponseRedirect('/?%s' % urllib.urlencode((('author',p.author),('title',p.title),('print','true'))))

def save(request):
    p = Puzzle.fromPOST(request.POST)
    t = get_template('xpf.xml')
    html = t.render(RequestContext(request, {'puzzle': p}))
    if p.author != "":
        atname = p.author + "-" + p.title
        atname = atname.replace('/','_')
        atname = atname.replace('.','_')
        atname = atname.replace(' ','_')
        atname = atname.lower()
        author = p.author
    else:
        atname = request.META['REMOTE_ADDR']
        author = atname
    title = p.title
    if request.POST.has_key('solver'):
        table = SolvePuzzles
        atname = request.POST['solver'] + '-' + atname
    else:
        table = RawPuzzles
    puzzles = table.objects.filter(author_title=atname)
    if len(puzzles) == 0:
        puz = table(author_title=atname)
    else:
        puz = puzzles[0]
    puz.contents = html
    puz.save()
    logger = logging.getLogger('xw.access')
    logger.info(" save request from %s for %s" % (request.META['REMOTE_ADDR'], atname));
    return HttpResponseRedirect('/?%s' % urllib.urlencode((('author',author),('title',title))))

def retrieve(request):
    author=request.POST["author"]
    title=request.POST["title"]
    logger = logging.getLogger('xw.access')
    if request.POST.has_key('solver'):
        solver = request.POST['solver']
        logger.info(" retrieve request from %s for Author: %s, Title: %s Solver: %s" % (request.META['REMOTE_ADDR'], author, title, solver));
        return HttpResponseRedirect('/?%s' % urllib.urlencode((('author',author),('title',title),('solver',solver))))
    else:
        logger.info(" retrieve request from %s for Author: %s, Title: %s" % (request.META['REMOTE_ADDR'], author, title));
        return HttpResponseRedirect('/?%s' % urllib.urlencode((('author',author),('title',title))))
    
def solve(request):
    author=request.POST["author"]
    title=request.POST["title"]
    logger = logging.getLogger('xw.access')
    logger.info(" solve request from %s for Author: %s, Title: %s" % (request.META['REMOTE_ADDR'], author, title));
    return HttpResponseRedirect('/?%s' % urllib.urlencode((('author',author),('title',title),('solve','true'))))
    
def download_xpf(request):
    p = Puzzle.fromPOST(request.POST)
    t = get_template('xpf.xml')
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html, content_type='text/xml')

def from_xpf(request):
    xml_handle = urllib.urlopen(request.POST["xpfurl"])
    xmldata = xml_handle.read()
    p = Puzzle.fromXML(xmldata)
    if p.size < 18:
        t = get_template('puzzle.html')
    else:
        t = get_template('puz21.html')
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)

def download_puz(request):
    t = get_template('puz.bin')
    p = Puzzle.fromPOST(request.POST)
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html, content_type='text/file')

def from_puz(request):
    t = get_template('puzzle.html')
    puz_handle = urllib.urlopen(request.POST["puzurl"])
    p = Puzzle.fromPUZ(puz_handle.read())
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)

def mobile_find(request):
    t = get_template('mxwf.html')
    html = t.render(RequestContext(request,{}))
    return HttpResponse(html)

def doc(request):
    t = get_template('doc.html')
    html = t.render(RequestContext(request,{}))
    return HttpResponse(html)

def newcryptic(request):
    t = get_template('puzzle.html')
    gridstrs = Grid.objects.filter(type=1)
    p = Puzzle.fromGrid(gridstrs[randrange(len(gridstrs))].format)
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)

def newus(request):
    t = get_template('puzzle.html')
    gridstrs = Grid.objects.filter(Q(format__startswith='15u'))
    p = Puzzle.fromGrid(gridstrs[randrange(len(gridstrs))].format)
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)
