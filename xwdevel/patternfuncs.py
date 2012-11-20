def suggest_words(request):
    logger = logging.getLogger('xw.access')
    logger.info(" words  request from %s for %s" % (request.META['REMOTE_ADDR'], request.GET["pattern"]));
    pat = request.GET["pattern"]
    length = len(pat)
    resp = ''
    pat = pat.replace('0','.')
    for wd in patterns.words(pat):
        resp = resp + wd + "&"
        if lines > 10:
            break

    resp = resp.rstrip('&')
    words.close()
    return HttpResponse(resp)

alph = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']

def score(word, xings):
    score = 1.0
    length = len(word)
    for i in range(length):
        pattern = xings[i][2][0:xings[i][0] - 1] + word[i:i+1] + xings[i][2][xings[i][0]:] 
        pattern = pattern.lower()
        patscore = patterns.patcount(pattern)
        if patscore == 0:
            try:
                if patterns.wds[len(pattern) - 3].has_key(pattern):
                    patscore = 1
            except:
                pass
        if patscore == 0:
            patscore = 0.0001
        score = score * patscore
    return score
def ranked_words_internal(request):
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
        pat = active_clue.ans
        length = len(pat)
        pat = pat.lower().replace('?','.')
        scores = {}
        for wd in patterns.words(pat):
            word_matches.append((patterns.wds[length-3][wd], wd))
        if not p.type == 'cryptic':
            for match_item in word_matches:
                scores[match_item[1]] = score(match_item[1], xings)
            word_matches.sort(lambda x,y: cmp(scores[y[1]], scores[x[1]]))
        resp = '&'.join(x[0] for x in word_matches)
    return HttpResponse(resp)

