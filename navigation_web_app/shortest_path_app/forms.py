from django import forms

class CarDimensionsForm(forms.Form):
    # height = forms.FloatField(label='Height [m]',initial = 0.0)
    # width = forms.FloatField(label='Width [m]',initial = 0.0)
    weight = forms.FloatField(label='Weight [kg]',initial = 0.0)