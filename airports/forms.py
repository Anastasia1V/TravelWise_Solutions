# airports/forms.py
from django import forms

class AirportForm(forms.Form):
    icao = forms.CharField(label='ICAO код', max_length=4)