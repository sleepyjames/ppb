from time import time
from datetime import date

from django.core.urlresolvers import reverse

from search.indexes import DocumentModel
from search.fields import TextField, IntegerField, DateField


class CodeSnippetDocument(DocumentModel):
    "A search document describing a code snippet"
    title = TextField()
    code = TextField()
    language_id = IntegerField()
    language_readable = TextField()
    creator_email = TextField()
    created = DateField()
    modified = DateField()


    def absolute_url(self):
        """Bit of redundancy here since this is also on
        `snippets.models.CodeSnippet` so that could just be parameterised to
        take kwargs or something.
        """
        if self.doc_id:
            kwargs = {'snippet_id': int(self.doc_id)}
            return reverse('snippets:snippet-detail', kwargs=kwargs)
