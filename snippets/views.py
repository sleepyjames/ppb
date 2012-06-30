import logging

from google.appengine.ext import db
from google.appengine.api import users

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


def get_current_user():
    "Quick implementation for getting the current user object"
    # TODO: do this properly

    u = users.get_current_user()
    if not u:
        return u

    id = u.user_id()
    email = u.email()

    db_u = User.get_by_key_name(str(id))
    if db_u is None:
        db_u = User(key_name=str(id), email=email)
        db_u.put()
    return db_u


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
            creator_email=s.creator.email
        ))
    i.add(docs)

    return HttpResponse('Done')


def _purge(request):
    "Debug view for purging all documents from the snippets search index"
    # TODO: remove

    i = Index(name='snippets')
    i.purge()
    return HttpResponse('Done')


class Home(TemplateView):
    """Shows the 5 latest snippets along with the 5 latest search results for
    any search if one has been performed.
    """
    template_name = 'snippets/index.html'

    def get_context_data(self, **kwargs):
        ctx = super(Home, self).get_context_data(**kwargs)

        # Mainly for testing my search API wrapper
        q = self.request.GET.get('q', '')
        if q:
            query = Index(name='snippets').search(CodeSnippetDocument)
            query = query.keywords(q)
            ctx['results'] = query[:5]
            ctx['results_count'] = query.count()

        ctx.setdefault('results', [])
        ctx.setdefault('results_count', 0)
        
        ctx['q'] = q
        ctx['latest_snippets'] = CodeSnippet.all().order('modified').fetch(5)

        return ctx

home = Home.as_view()


class SnippetDetail(TemplateView):
    "Detail view for a single snippet"
    template_name = 'snippets/detail.html'

    def get_context_data(self, **kwargs):
        code_snippet = get_snippet_or_404_on_error(self.kwargs.get('snippet_id'))

        if code_snippet is None:
            raise Http404()

        ctx = super(SnippetDetail, self).get_context_data(**kwargs)
        ctx['snippet'] = code_snippet
        return ctx

snippet_detail = SnippetDetail.as_view()


def edit_snippet(request, snippet_id=None):
    "Edit or create a code snippet"
    # TODO: tidy this shit up, it's mainly all left over from testing

    template_name = 'snippets/edit.html'

    ctx = {}

    if snippet_id is not None:
        form_action = reverse(
            'snippets:edit-snippet',
            kwargs={'snippet_id':snippet_id}
        )
    else:
        form_action = reverse('snippets:new-snippet')

    ctx['form_action'] = form_action

    if request.method == 'GET':
        initial_data = {}

        if snippet_id is not None:
            # TODO: use `get_snippet_or_404_on_error` here
            snippet = CodeSnippet.get_by_id(int(snippet_id))
            if snippet is None:
                raise Http404()
            initial_data.update(db.to_dict(snippet))

        form = CodeSnippetForm(initial=initial_data, auto_id=False)
        ctx['form'] = form

        return render_to_response(
            template_name,
            context_instance=RequestContext(request, ctx)
        )

    form = CodeSnippetForm(request.POST)

    if form.is_valid():
        if snippet_id is None:
            # We're creating a snippet
            snippet = CodeSnippet()
        else:
            snippet = get_snippet_or_404_on_error(snippet_id)
            if snippet is None:
                raise Http404()

        for field_name, clean_val in form.cleaned_data.items():
            setattr(snippet, field_name, clean_val)

        current_user = get_current_user()
        if not snippet.is_saved():
            snippet.creator = current_user
        snippet.modifier = current_user

        key = snippet.put()

        snippet_doc = CodeSnippetDocument(
            doc_id=key.id(),
            title=snippet.title,
            code=snippet.code,
            language_id=snippet.language,
            language_readable=snippet.get_language(),
            creator_email=snippet.creator.email
        )

        index = Index(name='snippets')
        index.add(snippet_doc)

        return HttpResponseRedirect(
            reverse('snippets:snippet-detail', kwargs={'snippet_id':key.id()})
        )

    ctx['form'] = form

    return render_to_response(
        template_name,
        context_instance=RequestContext(request, ctx)
    )
