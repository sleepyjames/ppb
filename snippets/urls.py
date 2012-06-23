from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns(
    'snippets',
    url(r'^$', 'views.home', {}, name='home'),
)

