from django import forms
from django.forms.formsets import formset_factory

MATCH_CRITERIA = (
    ('e-i', 'Compatible expertise and interests (from registration forms)'),
    ('similar-topics', 'Similar research topics (from NSF abstracts)'),
    ('serve-my-interest', 'Serve one participants interests well (from registration forms)'),
    ('dissimilar-topics', 'Dissimilar research topics (from NSF abstracts)'),
    ('bug', 'Must have been a bug in the implementation'))

MATCH_QUALITY = (
    ('0', 'Unsatisfactory (waste of time)'),
    ('1', 'Acceptable (reasonable conversation)'),
    ('2', 'Worthwhile (learned something useful)'),
    ('3', 'Valuable (found someone I expect to keep in contact with and possibly collaborate)'),
    ('4', 'Smashing Success (started a new collaboration)'))

class RatingForm(forms.Form):
    participants = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple(), choices=[], label='Participants (uncheck any who did not participate)')
    guessreason = forms.ChoiceField(choices=MATCH_CRITERIA, widget=forms.RadioSelect, label='Why do you think you were matched?')
    matchquality = forms.ChoiceField(choices=MATCH_QUALITY, widget=forms.RadioSelect, label='How good was this match?')
    comments = forms.CharField(max_length=1024,label='Comments:', widget=forms.Textarea(attrs={'cols': 70, 'rows': 4}))
