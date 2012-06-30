from google.appengine.api import users

from django.core.urlresolvers import reverse

from views import get_current_user


def put_user_in_context(request):
    ctx = {}
    ctx['user'] = get_current_user()
    ctx['login_url'] = users.create_login_url(request.path_info)
    ctx['logout_url'] = users.create_logout_url(reverse('snippets:home'))
    return ctx
