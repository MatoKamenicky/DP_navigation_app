from django import forms

class CarDimensionsForm(forms.Form):
    height = forms.DecimalField(label='Height (in meters)')
    width = forms.DecimalField(label='Width (in meters)')
    weight = forms.DecimalField(label='Weight (in kilograms)')