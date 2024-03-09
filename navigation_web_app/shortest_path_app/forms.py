from django import forms
from .models import Coordinates

class CoordinatesForm(forms.ModelForm):
    class Meta:
        model = Coordinates
        fields = ['latitude', 'longitude']