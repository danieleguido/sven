from django import forms
from sven.models import Corpus, Document, Segment, Profile



class LoginForm(forms.Form):
  username = forms.CharField(max_length=32, widget=forms.TextInput)
  password = forms.CharField(max_length=64, label='Password', widget=forms.PasswordInput(render_value=False))



class CorpusForm(forms.ModelForm):
  class Meta:
    model = Corpus
    exclude = ['owners','slug']



class DocumentForm(forms.ModelForm):
  class Meta:
    model = Document
    exclude = ['corpus', 'mimetype', 'slug']



class ProfileForm(forms.ModelForm):
  firstname = forms.CharField(max_length=32, widget=forms.TextInput, required=False)
  lastname = forms.CharField(max_length=32, widget=forms.TextInput, required=False)
  
  class Meta:
    model = Profile



class CorpusSegmentForm(forms.Form):
  cluster = forms.CharField(max_length=128)
  status = forms.ChoiceField(choices=Segment.STATUS_CHOICES)
