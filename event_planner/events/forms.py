from django import forms
from .models import Event, RSVP, Comment


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'time', 'location']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the event title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter a brief description of the event',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the event location',
            }),
        }

    def clean_date(self):
        """Ensure the event date is not in the past."""
        date = self.cleaned_data.get('date')
        if date and date < forms.fields.datetime.date.today():
            raise forms.ValidationError("The event date cannot be in the past.")
        return date


class RSVPForm(forms.ModelForm):
    class Meta:
        model = RSVP
        fields = ['status']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'rating']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 0, 'max': 5}),
        }
