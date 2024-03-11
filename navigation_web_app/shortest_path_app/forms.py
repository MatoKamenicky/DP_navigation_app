from django import forms
from .models import Coordinates

class CoordinatesForm(forms.ModelForm):
    class Meta:
        model = Coordinates
        fields = ['start_lat', 'start_lon', 'end_lat', 'end_lon']
        labels = {
            'start_lat': 'Start Latitude',
            'start_lon': 'Start Longitude',
            'end_lat': 'End Latitude',
            'end_lon': 'End Longitude',
        }