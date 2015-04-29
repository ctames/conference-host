from django import forms

class DocForm(forms.Form):
    docfile = forms.FileField(
        label='Please upload a txt or pdf file'
    )

class UrlForm(forms.Form):
    baseurl = forms.URLField(
        label='Please provide a link to your pdf'
    )

class FileChoice(forms.Form):
    choice = []
    files = forms.MultipleChoiceField(choices = choice, widget = forms.CheckboxSelectMultiple,)
    def __init__(self, options, *args, **kwargs):
        super(FileChoice, self ).__init__(*args, **kwargs)
        self.fields['files'] = forms.MultipleChoiceField(choices = options, widget = forms.CheckboxSelectMultiple,)


