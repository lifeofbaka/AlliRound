from django import forms
from .models import Flight 


class FlightSearchForm(forms.ModelForm):
    class Meta: 
        model = Flight
        fields = ['departure_text', 'arrival_text', 'departure_date', 'return_date']

        widgets = {'departure_date': forms.DateInput(attrs={'type': 'date'}),
                   'return_date': forms.DateInput(attrs={'type': 'date'})}
        