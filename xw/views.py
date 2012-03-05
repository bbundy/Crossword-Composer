from __future__ import with_statement
from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django import forms
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_protect
from django.utils.encoding import smart_unicode, smart_str
from django.template import RequestContext
from subprocess import Popen, PIPE
from xwcore import Puzzle
from xword.models import Grid, RawPuzzles, SolvePuzzles, Clue, Answer, Pattern
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from random import randrange
from django.db.models import Q
import logging
import urllib
import re
from wordnik import Wordnik
import sys
sys.path.append("/usr/local/src/wordnik")
sys.path.append("/usr/local/src/wordnik/api")
from APIClient import APIClient
from WordAPI import WordAPI
from WordsAPI import WordsAPI
import model
import time
import puz
import random


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

def pub_words(request):
    start_time = time.time()
    resp = ''
    word_matches = []
    clue = request.POST['active'] 
    (n1,ad,pos) = clue.split('-')
    p = Puzzle.fromPOST(request.POST)
    active_clue = p.clue_from_str(n1, ad)
    if active_clue:
        pat = active_clue.ans.lower()
        q = Answer.objects.extra(where=['answer LIKE "%s"' % pat.replace('?','_')])
        q = q.order_by('count').reverse()
        for r in q.all():
            word_matches.append(r.answer.lower())
        logger = logging.getLogger('xw.access')
        logger.info(" published words  request from %s for %s (%s) took %f seconds" % (request.META['REMOTE_ADDR'], request.POST["active"], pat, time.time() - start_time));
    resp = '&'.join(word_matches)
    return HttpResponse(resp)
    
def fill(request):
    resp = ''
    word_matches = []
    p = Puzzle.fromPOST(request.POST)
    stackstr = request.POST["fill-stack"]
    if stackstr == "":
        stack = p.initial_stack()
    else:
        stack = stackstr.split(',')
    guide = request.POST['fill-guide']
    if guide == 'on':
        clue = request.POST['active'] 
        (n1,ad,pos) = clue.split('-')
        active_clue = p.clue_from_str(n1, ad)
    else:
        active_clue = p.fill_clue(stack)
    if active_clue:
        pat = active_clue.ans.lower()
        q = Answer.objects.extra(where=['answer LIKE "%s"' % pat.replace('?','_')])
        q = q.order_by('count').reverse()
        for r in q.all():
            word_matches.append(r.answer.lower())
        if pat == '?' * len(pat):
            scores={}
            xings = p.clue_xings(active_clue)
            for word in word_matches:
                wordscore = 1.0
                for j in range(len(word)):
                    pattern = xings[j][2][0:xings[j][0] - 1] + word[j:j+1].upper() + xings[j][2][xings[j][0]:] 
                    try:
                        patscore_obj = Pattern.objects.get(pattern=pattern)
                        patscore = patscore_obj.count
                    except ObjectDoesNotExist:
                        patscore = Answer.objects.extra(where=['answer LIKE "%s"' % pattern.replace('?','_')]).count()
                        p_obj = Pattern(pattern=pattern, count=patscore)
                        p_obj.save()
                    wordscore *= patscore
                    if wordscore == 0:
                        break
                if wordscore > 0:
                    scores[word] = wordscore
            word_matches = []
            ct = 0
            for wd in sorted(scores.keys(), lambda x,y: cmp(scores[y], scores[x])):
                word_matches.append(wd)
                ct += 1
                if ct > 100:
                    break

                
        if len(word_matches) > 0:
            resp = fill_resp(p, word_matches, active_clue, "", stack)
        if len(word_matches) == 0 or resp == None:
            int_hash = {}
            cross_hash = p.cross_hash(active_clue)
            for i in range(len(pat)):
                if not pat[i:i+1] == '?':
                    cross = cross_hash["%d-%s-%d" % (active_clue.num, active_clue.dir, i+1)].split('-')
                    int_hash['-'.join(cross[0:2])] = 1
            do_list = ""
            got_int = False
            while True:
                last = None
                try:
                    last = stack.pop().split('&')
                except Exception:
                    pass
                if last == None or last == '' or len(last) < 3:
                    resp = "unfillable"
                    break
                if len(last) >= 3:
                    (num, ad) = last[0].split('-')
                    clue = p.clue_from_str(num,ad)
                    clue.ans = last[1]
                    last_xings = p.clue_xings(clue)
                    for i in range(clue.length):
                        xing_pos = last_xings[i][0]
                        if not clue.ans[i:i+1] == last_xings[i][2][xing_pos-1:xing_pos]:
                            (num, ad) = last_xings[i][3].split('-')
                            xing_clue = p.clue_from_str(num,ad)
                            xing_clue.ans = xing_clue.ans[0:xing_pos-1] + clue.ans[i:i+1] + xing_clue.ans[xing_pos:]
                    if not do_list == "":
                        do_list += "/"
                    do_list += "%s&%s" % (last[0], last[1])
                    if (last[2] == '') or ((not got_int) and (not int_hash.has_key(last[0]))):
                        if int_hash.has_key(last[0]):
                            got_int = True
                        continue;
                    else:
                        resp = fill_resp(p, last[2:], clue, do_list, stack)
                break
            
    return HttpResponse(resp)

def fill_resp(p, matches, active_clue, do_list, stack):
    for i in range(len(matches)):
        word = matches[i]
        poss = True;
        xings = p.clue_xings(active_clue)
        wd_stack = []
        wd_do_list = ""
        for j in range(len(word)):
            pattern = xings[j][2][0:xings[j][0] - 1] + word[j:j+1].upper() + xings[j][2][xings[j][0]:] 
            if pattern.find('?') == -1:
                continue
            try:
                patscore_obj = Pattern.objects.get(pattern=pattern)
                patscore = patscore_obj.count
            except ObjectDoesNotExist:
                patscore = Answer.objects.extra(where=['answer LIKE "%s"' % pattern.replace('?','_')]).count()
                p_obj = Pattern(pattern=pattern, count=patscore)
                p_obj.save()

            if patscore == 0:
                poss = False
                break
               
            if patscore == 1:
                xwd = Answer.objects.extra(where=['answer LIKE "%s"' % pattern.replace('?','_')]).all()[0].answer.lower()
                if not wd_do_list == "":
                    wd_do_list += "/"
                wd_do_list += "%s&%s" % (xings[j][3], xwd)
                wd_stack.append("%s&%s&%s" % (xings[j][3], pattern, ""))
        if poss:
            if not do_list == "":
                do_list += "/"
            do_list += "%d-%s&%s" % (active_clue.num, active_clue.dir, word)
            stack.append('%d-%s&%s&%s' % (active_clue.num, active_clue.dir, active_clue.ans, '&'.join(matches[i+1:])))
            stack += wd_stack
            if not wd_do_list == "":
                do_list += '/' + wd_do_list
            resp = '%s:%s' % (do_list, ','.join(stack))
            return resp
        else:
            continue
    try:
        while True:
            last = stack.pop().split('&')
            if len(last) > 2 and (not last[2] == ''):
                break
            if not do_list == "":
                do_list += "/"
            do_list += "%s&%s" % (last[0], last[1])
        if not do_list == '':
            do_list += '/'
        do_list += "%s&%s" % (last[0], last[2])
        stack.append('%s&%s&%s' % (last[0], last[1], '&'.join(last[3:])))
        resp = "%s:%s" % (do_list, ','.join(stack))
        return resp
    except Exception as e:
        return ""
    
apiKey="2e17a1567a9f6bc3792010e8e16057aa32d96f10e55d58b52"
wdnk_oldclient = Wordnik(api_key=apiKey, username="bbundy", password="rbb2wdnk")
wdnk_client = APIClient(apiKey, 'http://api.wordnik.com/v4')
wdnk_words = WordsAPI(wdnk_client)
wdnk_word = WordAPI(wdnk_client)

def ranked_words(request):
    start_time = time.time()
    resp = ''
    clue = request.POST['active'] 
    (n1,ad,pos) = clue.split('-')
    p = Puzzle.fromPOST(request.POST)
    active_clue = p.clue_from_str(n1, ad)
    if active_clue:
        word_matches = []
        pat = active_clue.ans
        length = len(pat)
        pat = pat.lower()
        scores = {}
        wi = model.WordsSearchInput.WordsSearchInput()
        wi.query = pat
        wi.caseSensitive = False
        wi.limit = 300
        wi.minLength = length
        wi.maxLength = length
        res = wdnk_words.searchWords(wi)
        logger = logging.getLogger('xw.access')
        logger.info(" ranked words  request from %s for %s (%s) took %f seconds" % (request.META['REMOTE_ADDR'], request.POST["active"], pat, time.time() - start_time));
        if res:
            for r in res:
                word_matches.append((r.wordstring, r.wordstring))
    resp = '&'.join(x[0] for x in word_matches)
    return HttpResponse(resp)

def list_words(request):
    start_time = time.time()
    resp = ''
    clue = request.POST['active'] 
    (n1,ad,pos) = clue.split('-')
    p = Puzzle.fromPOST(request.POST)
    active_clue = p.clue_from_str(n1, ad)
    if active_clue:
        word_matches = []
        res = None
        logger = logging.getLogger('xw.access')
        logger.info(" list words  request from %s for %s (%s) took %f seconds" % (request.META['REMOTE_ADDR'], request.POST["active"], pat, time.time() - start_time));
        if res:
            for r in res:
                word_matches.append((r.wordstring, r.wordstring))
    resp = '&'.join(x[0] for x in word_matches)
    return HttpResponse(resp)

swagger = True

def definition(request):
    resp = ''
    clue = request.POST['active'] 
    (n1,ad,pos) = clue.split('-')
    p = Puzzle.fromPOST(request.POST)
    active_clue = p.clue_from_str(n1, ad)
    if active_clue:
        if swagger:
            wd = model.WordDefinitionsInput.WordDefinitionsInput()
            wd.word = active_clue.ans.lower()
            word = wd.word
            wd.sourceDictionaries = "all"
            wd.useCanonical = True
            wd.includeRelated = True
            res = wdnk_word.getDefinitions(wd)
            if res:
                for r in res:
                    resp += "<b>%s</b> <i>(%s)</i> - %s<br><i> - %s</i><br>--------<br>" % (r.word, r.partOfSpeech, r.text, r.attributionText)
        else:
            word = active_clue.ans.lower()
            res = wdnk_oldclient.word_get_definitions(word, useCanonical=True)
            if res and res.has_key("definitions"):
                for r in res["definitions"]:
                    resp += "<b>%s</b> - %s<br><i> - %s</i><br>--------<br>" % (word, r['text'], r['attributionText'])
    logger = logging.getLogger('xw.access')
    logger.info(" definition request from %s for %s: %s" % (request.META['REMOTE_ADDR'], request.POST["active"], active_clue.ans));
    if resp == '':
        resp = "No definitions found for '%s'" % word
    return HttpResponse(resp)

def examples(request):
    resp = ''
    clue = request.POST['active'] 
    (n1,ad,pos) = clue.split('-')
    p = Puzzle.fromPOST(request.POST)
    active_clue = p.clue_from_str(n1, ad)
    if active_clue:
        if swagger:
            wd = model.WordExamplesInput.WordExamplesInput()
            wd.word = active_clue.ans.lower()
            word = wd.word
            wd.useCanonical = True
            wd.limit = 20
            res = wdnk_word.getExamples(wd)
            if res and res.examples:
                for r in res.examples:
                    if not hasattr(r,"year") or r.year == None:
                        r.year = ""
                    text = r.text.replace(word,"<font color=red>%s</font>" % word)
                    if r.url:
                        url = "<a href='%s' target=_blank>%s</a>" % (r.url, r.title)
                    else:
                        url = r.title
                    resp += "%s<br>%s - %s<br>--------<br>" % (text, r.year, url)
        else:
            word = active_clue.ans.lower()
            res = wdnk_oldclient.word_get_examples(word, useCanonical=True)
            if res and res.has_key("examples"):
                for r in res["examples"]:
                    text = r['text'].replace(word,"<font color=red>%s</font>" % word)
                    if r.has_key('year'):
                        year = r["year"]
                    else:
                        year = ""
                    resp += "%s<br>%s - <a href='%s' target=_blank>%s</a><br>--------<br>" % (text, year, r['url'], r['title'])
    logger = logging.getLogger('xw.access')
    logger.info(" examples request from %s for %s: %s" % (request.META['REMOTE_ADDR'], request.POST["active"], active_clue.ans));
    if resp == '':
        resp = "No examples found for '%s'" % word
    return HttpResponse(resp)

def auto_clue(request):
    resp = ''
    p = Puzzle.fromPOST(request.POST)
    for cl in p.clue:
        if cl.clue == '' and (cl.ans.find('?') == -1):
            table = Clue
            matches = table.objects.filter(answer=cl.ans)
            if len(matches) > 0:
                if not resp == '':
                    resp += '~'
                resp += "%d-%s|%s" % (cl.num, cl.dir, matches[random.randrange(len(matches))].text)
    return HttpResponse(resp)

def clues(request):
    resp = ''
    clue = request.POST['active'] 
    (n1,ad,pos) = clue.split('-')
    p = Puzzle.fromPOST(request.POST)
    active_clue = p.clue_from_str(n1, ad)
    if active_clue:
        word = active_clue.ans.lower()
        table = Clue
        cluelist = table.objects.filter(answer=word)
        if cluelist:
            for c in cluelist:
                resp += c.text + "<br> - "
                resp += c.puzzle.title + "<br> - "
                resp += c.puzzle.setter.username + " - " + c.puzzle.publisher.username + "<br>-------<br>"
    else:
        word = "(missing word)"
    logger = logging.getLogger('xw.access')
    logger.info(" clues request from %s for %s: %s" % (request.META['REMOTE_ADDR'], request.POST["active"], active_clue.ans));
    if resp == '':
        resp = "No clues found for '%s'" % word
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
                solver = request.GET['solver']
                atname = solver + '-' + atname
                table = SolvePuzzles
        puz = table.objects.filter(author_title=atname)
        if len(puz) > 0:
            p = Puzzle.fromXML(smart_str(puz[0].contents))
        if request.GET.has_key('print'):
            t = get_template('print.html') 
        if request.GET.has_key('printall'):
            t = get_template('printall.html') 
        if request.GET.has_key('xpf'):
            t = get_template('xpf.xml') 
    except:
        pass

    if p == None: 
        gridstrs = Grid.objects.filter(Q(format__startswith='15u'))
        p = Puzzle.fromGrid(gridstrs[randrange(len(gridstrs))].format)
    if solver:
        p.solver = solver
    html = t.render(RequestContext(request, {'puzzle': p}))
    if request.GET.has_key('xpf'):
        return HttpResponse(html, content_type='text/xml')
    else:
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

def do_save(p, request):
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

def print_cw(request):
    p = Puzzle.fromPOST(request.POST)
    do_save(p, request)
    logger = logging.getLogger('xw.access')
    logger.info(" print request from %s for '%s' by '%s'" % (request.META['REMOTE_ADDR'], p.title, p.author));
    return HttpResponseRedirect('/?%s' % urllib.urlencode((('author',p.author),('title',p.title),('print','true'))))

def print_cw_all(request):
    p = Puzzle.fromPOST(request.POST)
    do_save(p, request)
    logger = logging.getLogger('xw.access')
    logger.info(" printall request from %s for '%s' by '%s'" % (request.META['REMOTE_ADDR'], p.title, p.author));
    return HttpResponseRedirect('/?%s' % urllib.urlencode((('author',p.author),('title',p.title),('printall','true'))))

def save(request):
    p = Puzzle.fromPOST(request.POST)
    do_save(p, request)
    logger = logging.getLogger('xw.access')
    logger.info(" save request from %s for '%s' by '%s'" % (request.META['REMOTE_ADDR'], p.title, p.author));
    return HttpResponseRedirect('/?%s' % urllib.urlencode((('author',p.author),('title',p.title))))

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
    do_save(p, request)
    logger = logging.getLogger('xw.access')
    logger.info(" xpf request from %s for '%s' by '%s'" % (request.META['REMOTE_ADDR'], p.title, p.author));
    return HttpResponseRedirect('/?%s&xpf=true' % urllib.urlencode((('author',p.author),('title',p.title))))

def from_xpf(request):
    xml_handle = urllib.urlopen(request.POST["xpfurl"])
    xmldata = xml_handle.read()
    p = Puzzle.fromXML(xmldata)
    t = get_template('puzzle.html')
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)

def download_puz(request):
    p = Puzzle.fromPOST(request.POST)
    do_save(p, request)
    logger = logging.getLogger('xw.access')
    logger.info(" puz request from %s for '%s' by '%s'" % (request.META['REMOTE_ADDR'], p.title, p.author));
    pz = p.toPUZ()
    s = pz.tostring()
    response = HttpResponse(s, content_type='application/x-crossword')
    response['Content-Disposition'] = 'attachment; filename="%s.puz"' % p.title.replace(" ", "_")
    return response

def from_puz(request):
    t = get_template('puzzle.html')
    if request.POST.has_key("puzurl"):
        puz_handle = urllib.urlopen(request.POST["puzurl"])
        puz_data = puz_handle.read()
    else:
        puz_data = request.FILES["puzfile"].read()

    p = puz.load(puz_data)
    pz = Puzzle.fromPUZ(p)
    html = t.render(RequestContext(request, {'puzzle': pz}))
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
    if request.GET.has_key("size") and request.GET["size"] == "21":
        gridstrs = Grid.objects.filter(Q(format__startswith='21u'))
    else:
        gridstrs = Grid.objects.filter(Q(format__startswith='15u'))
    p = Puzzle.fromGrid(gridstrs[randrange(len(gridstrs))].format)
    html = t.render(RequestContext(request, {'puzzle': p}))
    return HttpResponse(html)
