from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns(
    'snippets',
    url(r'^$', 'views.home', {}, name='home'),
    url(r'^snippet/(?P<snippet_id>\d+)/$', 'views.snippet_detail', {},
        name='snippet-detail'),
    url(r'^snippet/new/$', 'views.new_snippet', {}, name='new-snippet'),
    url(r'^snippet/(?P<snippet_id>\d+)/edit/$', 'views.edit_snippet', {},
        name='edit-snippet'),

    url(r'^_purge/$', 'views._purge', {}, name='purge'),
    url(r'^_reindex/$', 'views._reindex', {}, name='reindex'),
)

