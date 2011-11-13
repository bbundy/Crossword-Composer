from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from xw.views import main_landing, sample2, member_request, thanks, suggest_words, print_cw, mobile_find
from xwdevel.views import download_xpf, from_xpf, doc, newus, newcryptic, download_puz, from_puz, save, retrieve, solve

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'xw.views.main_landing', name='home'),
    url(r'^/', main_landing),
    url(r'^s2/', sample2),
    url(r'^member-request/', member_request),
    url(r'^thanks/', thanks),
    url(r'^words/', suggest_words),
    url(r'^mxwf/', mobile_find),
    url(r'^print/', print_cw),
    url(r'^toxpf/', download_xpf),
    url(r'^fromxpf/', from_xpf),
    url(r'^topuz/', download_puz),
    url(r'^frompuz/', from_puz),
    url(r'^doc/', doc),
    url(r'^save/', save),
    url(r'^retrieve/', retrieve),
    url(r'^newus/', newus),
    url(r'^solve/', solve),
    url(r'^newcryptic/', newcryptic),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
