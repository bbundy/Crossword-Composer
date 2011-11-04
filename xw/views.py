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
from urllib import urlopen
from xword.models import Grid, RawPuzzles
from random import randrange
from django.db.models import Q
import logging

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
    pattern = request.GET["pattern"]
    pattern = pattern.replace('0','\\w[ \\-]*') + '.'
    words = open('/var/www/xw/UKACD17.TXT')
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

def main_landing(request):
    logger = logging.getLogger('xw.access')
    logger.info(" request from %s : %s" % (request.META['REMOTE_ADDR'], request.META['QUERY_STRING']));
    t = get_template('puzzle.html')
    p = None
    try:
        author = request.GET['author']
        title = request.GET['title']
        atname = author + "-" + title
        atname = atname.replace('/','_')
        atname = atname.replace('.','_')
        atname = atname.replace(' ','_')
        atname = atname.lower()
        puz = RawPuzzles.objects.filter(author_title=atname)
        if len(puz) > 0:
            p = Puzzle.fromXML(puz[0].contents)
    except:
        pass

    if p == None: 
        gridstrs = Grid.objects.filter(Q(format__startswith='15u'))
        p = Puzzle.fromGrid(gridstrs[randrange(len(gridstrs))].format)
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)

def sample2(request):
    t = get_template('puzzle.html')
    gridstr = Grid.objects.filter(type=1)[0].format
    p = Puzzle.fromGrid(gridstr)
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)

def print_cw(request):
    t = get_template('print.html')
    p = Puzzle.fromPOST(request.POST)
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)

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
    else:
        atname = request.REMOTE_ADDR
    puzzles = RawPuzzles.objects.filter(author_title=atname)
    if len(puzzles) == 0:
        puz = RawPuzzles(author_title=atname)
    else:
        puz = puzzles[0]
    puz.contents = html
    puz.save()
    return HttpResponse(html, content_type='text/xml')

def retrieve(request):
    author=request.POST["author"]
    title=request.POST["title"]
    atname = author + "-" + title
    atname = atname.replace('/','_')
    atname = atname.replace('.','_')
    atname = atname.replace(' ','_')
    atname = atname.lower()
    puz = RawPuzzles.objects.filter(author_title=atname)
    if len(puz) > 0:
        try :
            p = Puzzle.fromXML(puz[0].contents)
            if p.size < 18:
                t = get_template('puzzle.html')
            else:
                t = get_template('puz21.html')
            html = t.render(RequestContext(request, {'puzzle': p}))
            return HttpResponse(html)
        except Exception:
            return HttpResponseRedirect('/')
    return HttpResponseRedirect('/')
    
def download_xpf(request):
    p = Puzzle.fromPOST(request.POST)
    t = get_template('xpf.xml')
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html, content_type='text/xml')

def from_xpf(request):
    xml_handle = urlopen(request.POST["xpfurl"])
    p = Puzzle.fromXML(xml_handle.read())
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
    puz_handle = urlopen(request.POST["puzurl"])
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
