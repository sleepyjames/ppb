from google.appengine.ext import db
from google.appengine.api import users

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

    @classmethod
    def get_current(cls):
        "Get the current user based on the current users API GAIA account"
        # TODO: extend to use request.session, it'll be much faster
        user = users.get_current_user()
        if not user:
            return user

        id = str(user.user_id())
        email = user.email()

        # If we don't have a user in the database for this person, create
        # them now
        db_user = cls.get_by_key_name(id)
        if db_user is None:
            db_user = cls(key_name=id, email=email)
            db_user.put()
        return db_user


class Base(db.Model):
    "Takes care of created and modified timestamps and some handy methods"
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def get_or_create(cls, key_name_or_id, use_key=True):
        """Get or create an instance of this model class. If `use_key` is `True`
        then the model instance will be created with the given key as its
        `key_name`, otherwise it'll get a datastore-assigned id.
        """
        inst = cls.get(db.Key.from_path(cls, key_name_or_id))

        if inst is None:
            if use_key:
                inst = cls(key_name=key_name_or_id)
            else:
                inst = cls()
        return inst


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

    @property
    def comments(self):
        return Comment.all().filter('code_snippet =', self)


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
