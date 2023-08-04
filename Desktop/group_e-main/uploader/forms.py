from django import forms
from .models import Image


class ImageCreateForm(forms.ModelForm):

    class Meta:
        model = Image
        fields = ('title', 'file')
