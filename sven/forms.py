from django import forms
from sven.models import Corpus, Document



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