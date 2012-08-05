import logging
from datetime import datetime

from google.appengine.ext import db

from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.views.generic import TemplateView
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from snippets.models import CodeSnippet, User
from snippets.forms import CodeSnippetForm
from snippets.documents import CodeSnippetDocument

from search.indexes import Index


# Helpers. TODO: move these to a utils package probably.

def get_snippet_or_404_on_error(snippet_id):
    "Raise a 404 if the supplied key is invalid"
    try:
        snippet_id = int(snippet_id)
    except (TypeError, ValueError):
        raise Http404()

    return CodeSnippet.get_by_id(snippet_id)


def get_snippet_or_404(snippet_id):
    snippet = get_snippet_or_404_on_error(snippet_id)
    if snippet is None:
        raise Http404()
    return snippet


def index_snippet_with_search(snippet):
    snippet_doc = CodeSnippetDocument(
        doc_id=snippet.key().id(),
        title=snippet.title,
        code=snippet.code,
        language_id=snippet.language,
        language_readable=snippet.get_language(),
        creator_email=snippet.creator.email,
        created=datetime.now().date(),
        modified=snippet.modified.date(),
    )
    index = Index(name='snippets')
    index.add(snippet_doc)


def copy_snippet_from_form(form, snippet=None):
    if snippet is None:
        snippet = CodeSnippet()

    for field_name, clean_val in form.cleaned_data.items():
        setattr(snippet, field_name, clean_val)

    current_user = User.get_current()
    if not snippet.is_saved():
        snippet.creator = current_user
    snippet.modifier = current_user

    return snippet


def _reindex(request):
    "Debug view for reindexing all code snippets with search"
    # TODO: remove
    i = Index(name='snippets')

    docs = []
    for s in CodeSnippet.all():
        docs.append(CodeSnippetDocument(
            doc_id=s.key().id(),
            title=s.title,
            code=s.code,
            language_id=s.language,
            language_readable=s.get_language(),
            creator_email=s.creator.email,
            created=s.created.date(),
            modified=datetime.now().date(),
        ))
    i.add(docs)

    return HttpResponse('Done')


def _purge(request):
    "Debug view for purging all documents from the snippets search index"
    # TODO: remove

    i = Index(name='snippets')
    i.purge()
    return HttpResponse('Done')


class SearchMixin(object):
    """Will add search results of the given parameters to the view that
    inherits it from it.
    """
    # Configuration for searching

    # Default max number of items to return
    results_limit = 5

    # Index name to search and document class to use for results
    index_name = None
    document_class = None

    # URL param name for keyword search - is also the context name for the
    # keywords in the search
    query_param_name = 'q'
    # Allowed filter URL param names
    allowed_filters = {}

    # Context names for the list of results and the applied filters
    results_context_name = 'results'
    filters_context_name = 'filters'

    def get_filters(self):
        """Returns a dict of filters to apply to the search"""
        filters = {}
        for k, v in self.request.GET.items():
            if k in self.allowed_filters:
                filters[k] = v
        return filters

    def get_keywords(self):
        """Gets the keywords for the search"""
        return self.request.GET.get(self.query_param_name, '')

    def get_context_data(self, **kwargs):
        ctx = super(SearchMixin, self).get_context_data(**kwargs)

        query = None
        results_count_context_name = self.results_context_name+'_count'

        filters = self.get_filters()
        q = self.get_keywords()

        # The API wrapper should possibly handle the need for the following ifs
        if q or filters:
            query = Index(name=self.index_name).search(self.document_class)

        if query:
            if q:
                query = query.keywords(q)
            if filters:
                query = query.filter(**filters)

            ctx[self.results_context_name] = query[:self.results_limit]
            ctx[results_count_context_name] = query.count()

        ctx[self.query_param_name] = q
        ctx[self.filters_context_name] = filters
        ctx.setdefault(self.results_context_name, [])
        ctx.setdefault(results_count_context_name, 0)

        return ctx


class Home(SearchMixin, TemplateView):
    """Shows the 5 latest snippets along with the 5 latest search results for
    any search if one has been performed.
    """
    template_name = 'snippets/index.html'
    index_name = 'snippets'
    document_class = CodeSnippetDocument
    allowed_filters = ['language_id']

    def get_context_data(self, **kwargs):
        ctx = super(Home, self).get_context_data(**kwargs)
        ctx['latest_snippets'] = CodeSnippet.all().order('modified').fetch(5)

        return ctx

home = Home.as_view()


class SnippetDetail(TemplateView):
    "Detail view for a single snippet along with its last 5 comments"
    template_name = 'snippets/detail.html'

    def get_context_data(self, **kwargs):
        code_snippet = get_snippet_or_404(self.kwargs.get('snippet_id'))

        ctx = super(SnippetDetail, self).get_context_data(**kwargs)
        ctx['snippet'] = code_snippet
        ctx['comments'] = code_snippet.comments.fetch(5)
        return ctx

snippet_detail = SnippetDetail.as_view()


def new_snippet(request):
    "Creates a new code snippet"
    template_name = 'snippets/edit.html'

    if request.method == 'POST':
        form = CodeSnippetForm(request.POST)
        if form.is_valid():
            snippet = CodeSnippet()
            snippet = copy_snippet_from_form(form, snippet)
            snippet.put()
            index_snippet_with_search(snippet)
            
            return HttpResponseRedirect(reverse(
                'snippets:snippet-detail',
                kwargs={'snippet_id':snippet.key().id()}
            ))
    else:
        form = CodeSnippetForm()

    ctx = {}
    ctx['form'] = form
    ctx['form_action'] = reverse('snippets:new-snippet')

    return render_to_response(
        template_name,
        context_instance=RequestContext(request, ctx)
    )


def edit_snippet(request, snippet_id=None):
    "Edits an existing code snippet"
 
    if snippet_id is None:
        raise Http404()

    template_name = 'snippets/edit.html'

    if request.method == 'POST':
        form = CodeSnippetForm(request.POST)
        if form.is_valid():
            snippet = get_snippet_or_404(snippet_id)
            snippet = copy_snippet_from_form(form, snippet=snippet)
            snippet.put()
            index_snippet_with_search(snippet)

            return HttpResponseRedirect(reverse(
                'snippets:snippet-detail',
                kwargs={'snippet_id':snippet.key().id()}
            ))
    else:
        initial_data = {}
        snippet = get_snippet_or_404(snippet_id)
        initial_data.update(db.to_dict(snippet))
        form = CodeSnippetForm(initial=initial_data, auto_id=False)

    ctx = {}
    ctx['form'] = form
    ctx['form_action'] = reverse(
        'snippets:edit-snippet',
        kwargs={'snippet_id':snippet_id}
    )

    return render_to_response(
        template_name,
        context_instance=RequestContext(request, ctx)
    )
