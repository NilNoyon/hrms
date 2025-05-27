from django import forms
from .models import *

class FAItemForm(forms.ModelForm):

    class Meta:
        model = AssetItem
        fields = "__all__"

class FASubClassificationForm(forms.ModelForm):

    class Meta:
        model = AssetSubClassification
        fields = "__all__"

class FAAssetForm(forms.ModelForm):

    class Meta:
        model = Asset
        fields = '__all__'

class FAAssetAllocationForm(forms.ModelForm):

    class Meta:
        model = FAAssetAllocation
        fields = '__all__'
