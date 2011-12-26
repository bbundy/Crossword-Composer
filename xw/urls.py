from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from xwdevel.views import main_landing, member_request, thanks, print_cw, mobile_find, usegrid, ranked_words, definition, examples, print_cw_all
from xwdevel.views import download_xpf, from_xpf, doc, newus, newcryptic, download_puz, from_puz, save, retrieve, solve, gridedit
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'xwdevel.views.main_landing', name='home'),
    url(r'^/', main_landing),
    url(r'^member-request/', member_request),
    url(r'^thanks/', thanks),
    url(r'^rankedwords/', ranked_words),
    url(r'^definition/', definition),
    url(r'^examples/', examples),
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
    url(r'^gridedit/', gridedit),
    url(r'^usegrid/', usegrid),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
