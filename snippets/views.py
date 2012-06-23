from django.views.generic import TemplateView

#from snippets.models import


class Home(TemplateView):
    template_name = 'snippets/index.html'

home = Home.as_view()
