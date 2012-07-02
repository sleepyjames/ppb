from django.core.urlresolvers import reverse

from search.indexes import DocumentModel
from search.fields import TextField, IntegerField


class CodeSnippetDocument(DocumentModel):
    "A search document describing a code snippet"
    title = TextField()
    code = TextField()
    language_id = IntegerField(default=0)
    language_readable = TextField()
    creator_email = TextField()

    def absolute_url(self):
        """Bit of redundancy here since this is also on
        `snippets.models.CodeSnippet` so that could just be parameterised to
        take kwargs or something.
        """
        if self.doc_id:
            kwargs = {'snippet_id': int(self.doc_id)}
            reverse('snippets:snippet-detail', kwargs=kwargs)
