from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns(
    '',
    (r'', include('snippets.urls', namespace='snippets'),),
    (r'^i18n/', include('django.conf.urls.i18n'),),
)
