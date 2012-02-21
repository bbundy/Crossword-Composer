from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.views.generic.simple import direct_to_template, redirect_to
from django.shortcuts import redirect
from xw.views import main_landing, member_request, thanks, print_cw, mobile_find, usegrid, ranked_words, definition, examples, print_cw_all, fill, auto_clue
from xw.views import download_xpf, from_xpf, doc, newus, newcryptic, download_puz, from_puz, save, retrieve, solve, gridedit, clues, pub_words, list_words
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'xwdevel.views.main_landing', name='home'),
    url(r'^/', main_landing),
    url(r'^member-request/', member_request),
    url(r'^thanks/', thanks),
    url(r'^rankedwords/', ranked_words),
    url(r'^pubwords/', pub_words),
    url(r'^listwords/', list_words),
    url(r'^definition/', definition),
    url(r'^examples/', examples),
    url(r'^clues/', clues),
    url(r'^mxwf/', mobile_find),
    url(r'^print/', print_cw),
    url(r'^printall/', print_cw_all),
    url(r'^toxpf/', download_xpf),
    url(r'^fromxpf/', from_xpf),
    url(r'^topuz/', download_puz),
    url(r'^frompuz/', from_puz),
    url(r'^doc/', doc),
    url(r'^save/', save),
    url(r'^retrieve/', retrieve),
    url(r'^newcryptic/', newcryptic),
    url(r'^newus/', newus),
    url(r'^solve/', solve),
    url(r'^fill/', fill),
    url(r'^autoclue/', auto_clue),
    url(r'^gridedit/', gridedit),
    url(r'^usegrid/', usegrid),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^robots\.txt$', direct_to_template,
     {'template': 'robots.txt', 'mimetype': 'text/plain'}),
)
