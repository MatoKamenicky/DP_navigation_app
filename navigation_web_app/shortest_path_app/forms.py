from django import forms

class CarDimensionsForm(forms.Form):
    # height = forms.FloatField(label='Height [m]',initial = 0.0)
    # width = forms.FloatField(label='Width [m]',initial = 0.0)
    weight = forms.FloatField(initial=0.0, widget=forms.TextInput(attrs={'placeholder': 'Weight [t]', 'label': 'Weight [t]'}))
