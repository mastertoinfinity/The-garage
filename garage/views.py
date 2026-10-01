from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import BookingForm, ContactForm, SignUpForm
from .models import Booking, Review, Service


def home(request):
    return render(request, "garage/home.html", {
        "services": Service.objects.filter(is_active=True, is_featured=True)[:3],
        "reviews": Review.objects.filter(is_published=True)[:3],
    })


def services(request):
    return render(request, "garage/services.html", {"services": Service.objects.filter(is_active=True)})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Message received. Our team will be in touch shortly.")
        return redirect("contact")
    return render(request, "garage/contact.html", {"form": form})


def signup(request):
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready. Let's get your vehicle sorted.")
        return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def book_service(request):
    initial = {"service": request.GET.get("service")}
    form = BookingForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        booking.customer = request.user
        try:
            booking.full_clean()
        except Exception as error:
            form.add_error(None, error)
        else:
            booking.save()
            messages.success(request, "Your appointment request is in. We'll confirm it soon.")
            return redirect("booking_history")
    return render(request, "garage/booking_form.html", {"form": form})


@login_required
def dashboard(request):
    bookings = request.user.bookings.select_related("service")
    upcoming = [booking for booking in bookings if booking.is_upcoming][:3]
    return render(request, "garage/dashboard.html", {"upcoming": upcoming, "booking_count": bookings.count()})


@login_required
def booking_history(request):
    bookings = request.user.bookings.select_related("service").all()
    upcoming = [booking for booking in bookings if booking.is_upcoming]
    history = [booking for booking in bookings if not booking.is_upcoming]
    return render(request, "garage/booking_history.html", {"upcoming": upcoming, "history": history})