from django import forms
from django.conf import settings


class CodeSnippetForm(forms.Form):
    LANGUAGE_CHOICES = settings.PROGRAMMING_LANGUAGE_CHOICES.items()

    #id = forms.IntegerField(required=False)
    title = forms.CharField(max_length=500)
    code = forms.CharField(widget=forms.Textarea)
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES)

    def clean_language(self):
        return int(self.cleaned_data['language'])
