from django import forms

from twit.models import Account



class AccountForm(forms.Form):
  url = forms.URLField()
  corpus = forms.IntegerField()

  def clean_url(self):
    url = self.cleaned_data['url']
    
    if Account.get_twitter_account(url) is None:
      raise forms.ValidationError("please provide a valid twitter url")
    return url