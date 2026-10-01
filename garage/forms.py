from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Booking, ContactMessage, Service


class SignUpForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, label="First name")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "password1", "password2")


class BookingForm(forms.ModelForm):
    service = forms.ModelChoiceField(queryset=Service.objects.filter(is_active=True), empty_label="Choose a service")
    appointment_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    appointment_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))

    class Meta:
        model = Booking
        fields = ("service", "vehicle", "appointment_date", "appointment_time", "notes")
        widgets = {"notes": forms.Textarea(attrs={"rows": 4, "placeholder": "Anything we should know about your vehicle?"})}
        labels = {"vehicle": "Vehicle (year, make & model)", "notes": "Notes for our technicians"}

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data["appointment_date"]
        if appointment_date < timezone.localdate():
            raise forms.ValidationError("Choose today or a future date.")
        return appointment_date


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}