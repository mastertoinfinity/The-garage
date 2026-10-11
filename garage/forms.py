from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .models import Booking, ContactMessage, GarageLocation, Service


class SignUpForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, label="First name")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "password1", "password2")


class BookingForm(forms.ModelForm):
    service = forms.ModelChoiceField(queryset=Service.objects.filter(is_active=True), empty_label="Choose a service")
    location = forms.ModelChoiceField(queryset=GarageLocation.objects.filter(is_active=True), empty_label="Choose a garage location")
    appointment_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    appointment_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    vehicle_number = forms.CharField(max_length=20, label="Vehicle registration number", widget=forms.TextInput(attrs={"placeholder": "e.g. KA 01 AB 1234", "autocomplete": "off"}))

    class Meta:
        model = Booking
        fields = ("service", "location", "vehicle_type", "car_type", "vehicle_number", "vehicle", "appointment_date", "appointment_time", "notes")
        widgets = {"notes": forms.Textarea(attrs={"rows": 4, "placeholder": "Anything we should know about your vehicle?"})}
        labels = {"vehicle": "Vehicle details (year, make & model)", "vehicle_type": "Vehicle type", "car_type": "Car type", "notes": "Notes for our technicians"}

    def clean_vehicle_number(self):
        return self.cleaned_data["vehicle_number"].strip().upper()

    def clean(self):
        cleaned_data = super().clean()
        vehicle_type = cleaned_data.get("vehicle_type")
        car_type = cleaned_data.get("car_type")
        if vehicle_type == Booking.VehicleType.CAR and not car_type:
            self.add_error("car_type", "Choose your car type.")
        elif vehicle_type == Booking.VehicleType.BIKE and car_type:
            self.add_error("car_type", "Leave car type blank for a bike.")
        return cleaned_data

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


class BranchBookingActionForm(forms.Form):
    class Action(models.TextChoices):
        ACCEPT = "accept", "Accept booking"
        DECLINE = "decline", "Decline booking"
        UPDATE_INVOICE = "update_invoice", "Update invoice"
        COMPLETE = "complete", "Mark service complete"
        MARK_PAID = "mark_paid", "Mark payment received"
        MARK_READY = "mark_ready", "Mark vehicle ready for delivery"
        VERIFY_PAYMENT = "verify_payment", "Verify customer UPI payment"

    action = forms.ChoiceField(choices=Action.choices)
    final_price = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("0.01"),
        required=False,
        label="Final invoice amount (INR)",
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("action") in (self.Action.COMPLETE, self.Action.UPDATE_INVOICE) and cleaned_data.get("final_price") is None:
            self.add_error("final_price", "Enter the invoice amount.")
        return cleaned_data


class UpiPaymentConfirmationForm(forms.Form):
    payment_reference = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. 12-digit UPI Reference / UTR Number"}),
        label="UPI Reference / Transaction ID",
    )