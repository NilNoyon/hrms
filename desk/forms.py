from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from .models import *


class IssueAddForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ("ref", "description",
                  "issuer", "attachment", "status")

    def __init__(self, *args, **kwargs):
        super(IssueAddForm, self).__init__(*args, **kwargs)
        self.fields['attachment'].required = False
