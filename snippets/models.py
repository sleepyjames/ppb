from google.appengine.ext import db

from django.conf import settings
from django.core.urlresolvers import reverse


class KeyRequiredError(Exception):
    pass


class User(db.Model):
    "A reference to a user from the `google.appengine.api.users`"

    gaia_id = db.StringProperty()
    email = db.StringProperty()

    def __init__(self, *args, **kwargs):
        # Bit of a hack, but make sure that every `User` object is instantiated
        # with a `key_name` property. This doesn't happen when it's being
        # populated from datastore queries though, so check to see if it's
        # being created from the entity before doing the checking.
        if not kwargs.get('_from_entity'):
            key_name = kwargs.get('key_name')

            if key_name is None:
                raise KeyRequiredError('The User class requires the `key_name` '
                    'keyword arg to be passed at instantiation. It should be the '
                    'GAIA id of the user.')

            kwargs.pop('gaia_id', None)
            self.gaia_id = key_name
        super(User, self).__init__(**kwargs)


class Base(db.Model):
    "Takes care of created and modified timestamps"
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)


class CodeSnippet(Base):
    "Exactly what it says it is"

    CREATOR_COLLECTION_NAME = 'snippets_created_by_me'
    MODIFIER_COLLECTION_NAME = 'snippets_last_modified_by_me'

    title = db.StringProperty()
    code = db.TextProperty()
    language = db.IntegerProperty(choices=settings.PROGRAMMING_LANGUAGE_CHOICES)
    creator = db.ReferenceProperty(
        reference_class=User,
        collection_name=CREATOR_COLLECTION_NAME
    )
    modifier = db.ReferenceProperty(
        reference_class=User,
        collection_name=MODIFIER_COLLECTION_NAME
    )

    def get_language(self):
        "Return the readable version of this snippet's programming language"
        return settings.PROGRAMMING_LANGUAGE_CHOICES.get(self.language)

    def get_absolute_url(self):
        if self.is_saved():
            kwargs = {'snippet_id': self.key().id()}
            return reverse('snippets:snippet-detail', kwargs=kwargs)


class Comment(Base):
    "A comment on a code snippet"

    CREATOR_COLLECTION_NAME = 'comments'
    # This one is effectively pointless
    MODIFIER_COLLECTION_NAME = 'comments_'

    body = db.TextProperty()
    code_snippet = db.ReferenceProperty(reference_class=CodeSnippet,
        collection_name='comments')
    creator = db.ReferenceProperty(
        reference_class=User,
        collection_name=CREATOR_COLLECTION_NAME
    )
    modifier = db.ReferenceProperty(
        reference_class=User,
        collection_name=MODIFIER_COLLECTION_NAME
    )
