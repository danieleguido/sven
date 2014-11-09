from django import forms
from sven.models import Corpus, Document, Segment, Profile, Tag



class LoginForm(forms.Form):
  username = forms.CharField(max_length=128, widget=forms.TextInput)
  password = forms.CharField(max_length=64, label='Password', widget=forms.PasswordInput(render_value=False))



class TagsForm(forms.Form):
  type = forms.ChoiceField(choices=Tag.TYPE_CHOICES)
  tags = forms.RegexField(regex=r'^[\=\.\?\:\/\s\w,\-\_\']*$',label='tags' )



class CorpusForm(forms.ModelForm):
  class Meta:
    model = Corpus
    exclude = ['owners','slug']



class DocumentForm(forms.ModelForm):
  date = forms.DateTimeField(input_formats=['%Y-%m-%d'])
  tags = forms.CharField(required=False)

  class Meta:
    model = Document

    exclude = ['corpus', 'slug', 'language']



class ProfileForm(forms.ModelForm):
  firstname = forms.CharField(max_length=32, widget=forms.TextInput, required=False)
  lastname = forms.CharField(max_length=32, widget=forms.TextInput, required=False)
  
  class Meta:
    model = Profile



class CorpusSegmentForm(forms.Form):
  cluster = forms.CharField(max_length=128)
  status = forms.ChoiceField(choices=Segment.STATUS_CHOICES)



class UploadCSVForm(forms.Form):
    '''
    Handle CSV file upload
    '''
    file = forms.FileField()


class DocumentMetadataForm(forms.ModelForm):
  '''
  Cfr. sven/amnagement/command/start_job
  '''
  date = forms.DateTimeField(required=False)
  class Meta:
    model = Document
    exclude = ['corpus', 'slug', 'mimetype', 'abstract']
  