from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    BookingForm,
    BranchBookingActionForm,
    ContactForm,
    SignUpForm,
    UpiPaymentConfirmationForm,
)
from .models import Booking, GarageLocation, Review, Service


def health_check(request):
    db_healthy = True
    db_msg = "connected"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        db_healthy = False
        db_msg = str(e)
    
    return JsonResponse({
        "status": "healthy" if db_healthy else "unhealthy",
        "service": "the_garage",
        "database": db_msg,
        "timestamp": timezone.now().isoformat(),
        "version": "1.0.0",
    }, status=200 if db_healthy else 503)


def home(request):
    services = Service.objects.filter(is_active=True)
    featured = services.filter(is_featured=True)[:3]
    if not featured.exists():
        featured = services[:3]
    locations = GarageLocation.objects.filter(is_active=True)
    reviews = Review.objects.filter(is_published=True)[:3]
    return render(request, "garage/home.html", {
        "services": featured,
        "all_services": services,
        "locations": locations,
        "reviews": reviews,
    })


def services(request):
    return render(request, "garage/services.html", {"services": Service.objects.filter(is_active=True)})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Message received. Our team will be in touch shortly.")
        return redirect("contact")
    locations = GarageLocation.objects.filter(is_active=True)
    return render(request, "garage/contact.html", {"form": form, "locations": locations})


def signup(request):
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready. Let's get your vehicle sorted.")
        return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form})


def management_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        if GarageLocation.objects.filter(manager=request.user, is_active=True).exists():
            return redirect("branch_dashboard")
        return redirect("management_dashboard")

    form = AuthenticationForm(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if not user.is_staff:
            form.add_error(None, "This account does not have administrator access.")
        else:
            login(request, user)
            if GarageLocation.objects.filter(manager=user, is_active=True).exists():
                return redirect("branch_dashboard")
            return redirect("management_dashboard")
    return render(request, "garage/management_login.html", {"form": form})


@login_required
def management_dashboard(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Administrator access required.")
    if GarageLocation.objects.filter(manager=request.user, is_active=True).exists():
        return redirect("branch_dashboard")

    bookings = Booking.objects.select_related("customer", "service", "location")
    return render(request, "garage/management_dashboard.html", {
        "branch_count": GarageLocation.objects.filter(is_active=True).count(),
        "booking_count": bookings.count(),
        "pending_count": bookings.filter(status=Booking.Status.PENDING).count(),
        "confirmed_count": bookings.filter(status=Booking.Status.CONFIRMED).count(),
        "completed_count": bookings.filter(status=Booking.Status.COMPLETED).count(),
        "recent_bookings": bookings.order_by("-created_at")[:10],
        "locations": GarageLocation.objects.filter(is_active=True),
    })


@login_required
def management_booking_action(request, booking_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Administrator access required.")
    if request.method != "POST":
        return HttpResponse(status=405)
    booking = get_object_or_404(Booking.objects.select_related("customer", "service"), pk=booking_id)
    form = BranchBookingActionForm(request.POST)
    if form.is_valid():
        action = form.cleaned_data["action"]
        if action == BranchBookingActionForm.Action.ACCEPT and booking.status == Booking.Status.PENDING:
            booking.status = Booking.Status.CONFIRMED
            booking.save(update_fields=["status"])
            messages.success(request, f"Booking TG-{booking.pk:06d} for {booking.customer} accepted.")
        elif action == BranchBookingActionForm.Action.DECLINE and booking.status == Booking.Status.PENDING:
            booking.status = Booking.Status.DECLINED
            booking.save(update_fields=["status"])
            messages.success(request, f"Booking TG-{booking.pk:06d} for {booking.customer} declined.")
        elif action == BranchBookingActionForm.Action.UPDATE_INVOICE and booking.status in (Booking.Status.CONFIRMED, Booking.Status.COMPLETED):
            booking.final_price = form.cleaned_data["final_price"]
            booking.invoice_ready = True
            booking.save(update_fields=["final_price", "invoice_ready"])
            messages.success(request, f"Invoice updated to ₹{booking.final_price:.2f} for booking TG-{booking.pk:06d}.")
        elif action == BranchBookingActionForm.Action.COMPLETE and booking.status == Booking.Status.CONFIRMED:
            booking.status = Booking.Status.COMPLETED
            booking.final_price = form.cleaned_data["final_price"]
            booking.invoice_ready = True
            booking.save(update_fields=["status", "final_price", "invoice_ready"])
            messages.success(request, f"Service completed. Invoice TG-{booking.pk:06d} published for customer.")
        elif action == BranchBookingActionForm.Action.MARK_PAID:
            booking.is_paid = True
            booking.is_ready_for_delivery = True
            booking.paid_at = timezone.now()
            booking.payment_reference = booking.payment_reference or "Staff Verified Payment"
            booking.payment_pending_verification = False
            booking.save(update_fields=["is_paid", "is_ready_for_delivery", "paid_at", "payment_reference", "payment_pending_verification"])
            messages.success(request, f"Payment confirmed for TG-{booking.pk:06d}. Vehicle is marked ready for delivery.")
        elif action == BranchBookingActionForm.Action.MARK_READY:
            booking.is_ready_for_delivery = True
            booking.save(update_fields=["is_ready_for_delivery"])
            messages.success(request, f"Booking TG-{booking.pk:06d} marked as ready for delivery.")
        elif action == BranchBookingActionForm.Action.VERIFY_PAYMENT:
            booking.is_paid = True
            booking.is_ready_for_delivery = True
            booking.paid_at = timezone.now()
            booking.payment_pending_verification = False
            booking.payment_reference = booking.payment_reference or "UPI (8431699047@nyes)"
            booking.save(update_fields=["is_paid", "is_ready_for_delivery", "paid_at", "payment_pending_verification", "payment_reference"])
            messages.success(request, f"UPI payment verified for TG-{booking.pk:06d}. Vehicle marked ready for delivery! Customer will see the delivery notice.")
        else:
            messages.error(request, "That action is not available for this booking's current status.")
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect("management_dashboard")


@login_required
def book_service(request):
    initial = {"service": request.GET.get("service")}
    form = BookingForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        booking.customer = request.user
        booking.save()
        messages.success(request, "Your appointment request is in. We'll confirm it soon.")
        return redirect("booking_history")
    return render(request, "garage/booking_form.html", {"form": form})


@login_required
def dashboard(request):
    bookings = request.user.bookings.select_related("service", "location").all()
    upcoming = [booking for booking in bookings if booking.is_upcoming][:3]
    active_deliveries = [booking for booking in bookings if booking.is_vehicle_ready][:3]
    pending_verifications = [booking for booking in bookings if booking.payment_pending_verification and not booking.is_paid][:3]
    pending_payments = [booking for booking in bookings if booking.has_invoice and not booking.is_paid and not booking.payment_pending_verification][:3]
    return render(request, "garage/dashboard.html", {
        "upcoming": upcoming,
        "active_deliveries": active_deliveries,
        "pending_payments": pending_payments,
        "pending_verifications": pending_verifications,
        "booking_count": bookings.count(),
    })


@login_required
def booking_history(request):
    bookings = request.user.bookings.select_related("service").all()
    upcoming = [booking for booking in bookings if booking.is_upcoming]
    history = [booking for booking in bookings if not booking.is_upcoming]
    return render(request, "garage/booking_history.html", {"upcoming": upcoming, "history": history})


@login_required
def branch_dashboard(request):
    location = GarageLocation.objects.filter(manager=request.user, is_active=True).first()
    if location is None:
        raise Http404("No active garage branch is assigned to this account.")
    bookings = location.bookings.select_related("customer", "service", "location").all()
    return render(request, "garage/branch_dashboard.html", {"location": location, "bookings": bookings})


@login_required
def branch_booking_action(request, booking_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    location = GarageLocation.objects.filter(manager=request.user, is_active=True).first()
    if location is None:
        raise Http404("No active garage branch is assigned to this account.")
    booking = get_object_or_404(location.bookings.select_related("customer", "service"), pk=booking_id)
    form = BranchBookingActionForm(request.POST)
    if form.is_valid():
        action = form.cleaned_data["action"]
        if action == BranchBookingActionForm.Action.ACCEPT and booking.status == Booking.Status.PENDING:
            booking.status = Booking.Status.CONFIRMED
            booking.save(update_fields=["status"])
            messages.success(request, f"Booking for {booking.customer} accepted.")
        elif action == BranchBookingActionForm.Action.DECLINE and booking.status == Booking.Status.PENDING:
            booking.status = Booking.Status.DECLINED
            booking.save(update_fields=["status"])
            messages.success(request, f"Booking for {booking.customer} declined.")
        elif action == BranchBookingActionForm.Action.UPDATE_INVOICE and booking.status in (Booking.Status.CONFIRMED, Booking.Status.COMPLETED):
            booking.final_price = form.cleaned_data["final_price"]
            booking.invoice_ready = True
            booking.save(update_fields=["final_price", "invoice_ready"])
            messages.success(request, f"Invoice updated to ₹{booking.final_price:.2f} for booking TG-{booking.pk:06d}.")
        elif action == BranchBookingActionForm.Action.COMPLETE and booking.status == Booking.Status.CONFIRMED:
            booking.status = Booking.Status.COMPLETED
            booking.final_price = form.cleaned_data["final_price"]
            booking.invoice_ready = True
            booking.save(update_fields=["status", "final_price", "invoice_ready"])
            messages.success(request, f"Service completed. Invoice TG-{booking.pk:06d} is ready for the customer.")
        elif action == BranchBookingActionForm.Action.MARK_PAID:
            booking.is_paid = True
            booking.is_ready_for_delivery = True
            booking.paid_at = timezone.now()
            booking.payment_reference = booking.payment_reference or "Branch Verified Payment"
            booking.payment_pending_verification = False
            booking.save(update_fields=["is_paid", "is_ready_for_delivery", "paid_at", "payment_reference", "payment_pending_verification"])
            messages.success(request, f"Payment confirmed for TG-{booking.pk:06d}. Vehicle is marked ready for delivery.")
        elif action == BranchBookingActionForm.Action.MARK_READY:
            booking.is_ready_for_delivery = True
            booking.save(update_fields=["is_ready_for_delivery"])
            messages.success(request, f"Booking TG-{booking.pk:06d} marked as ready for delivery.")
        elif action == BranchBookingActionForm.Action.VERIFY_PAYMENT:
            booking.is_paid = True
            booking.is_ready_for_delivery = True
            booking.paid_at = timezone.now()
            booking.payment_pending_verification = False
            booking.payment_reference = booking.payment_reference or "UPI (8431699047@nyes)"
            booking.save(update_fields=["is_paid", "is_ready_for_delivery", "paid_at", "payment_pending_verification", "payment_reference"])
            messages.success(request, f"UPI payment verified for TG-{booking.pk:06d}. Vehicle marked ready for delivery!")
        else:
            messages.error(request, "That action is not available for this booking's current status.")
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect("branch_dashboard")


@login_required
def invoice_detail(request, booking_id):
    booking = get_object_or_404(
        request.user.bookings.select_related("service", "location"),
        pk=booking_id,
    )
    if not booking.has_invoice:
        raise Http404("The invoice is available after the service details are updated.")
    payment_form = UpiPaymentConfirmationForm()
    return render(request, "garage/invoice.html", {
        "booking": booking,
        "invoice_date": timezone.localdate(),
        "invoice_total": booking.effective_price,
        "payment_form": payment_form,
    })


@login_required
def pay_booking_upi(request, booking_id):
    if request.method != "POST":
        return HttpResponse(status=405)
    booking = get_object_or_404(
        request.user.bookings.select_related("service", "location"),
        pk=booking_id,
    )
    if not booking.has_invoice:
        raise Http404("The invoice is not yet ready for this booking.")
    if booking.is_paid:
        messages.info(request, "This booking is already marked as paid.")
        return redirect("invoice_detail", booking_id=booking.pk)
    form = UpiPaymentConfirmationForm(request.POST)
    ref = ""
    if form.is_valid():
        ref = form.cleaned_data.get("payment_reference", "").strip()
    booking.payment_pending_verification = True
    booking.is_paid = False
    booking.is_ready_for_delivery = False
    booking.payment_reference = ref or booking.payment_reference
    booking.save(update_fields=["payment_pending_verification", "payment_reference", "is_paid", "is_ready_for_delivery"])
    messages.success(
        request,
        f"UPI transaction reference '{booking.payment_reference}' submitted! The garage admin is verifying your payment. Once verified, your vehicle delivery message will appear.",
    )
    return redirect("invoice_detail", booking_id=booking.pk)


@login_required
def invoice_pdf(request, booking_id):
    booking = get_object_or_404(
        request.user.bookings.select_related("service", "location"),
        pk=booking_id,
    )
    if not booking.has_invoice:
        raise Http404("The invoice is available after the service details are updated.")
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left = 52
    y = height - 58

    pdf.setTitle(f"THE GARAGE invoice {booking.pk}")
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(left, y, "THE GARAGE")
    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(width - left, y + 5, f"INVOICE  TG-{booking.pk:06d}")
    y -= 22
    pdf.setFillColorRGB(.35, .35, .35)
    pdf.drawString(left, y, "SERVICE INVOICE")
    pdf.drawRightString(width - left, y, f"Issued {timezone.localdate():%d %b %Y}")
    y -= 24
    pdf.setStrokeColorRGB(.82, .82, .82)
    pdf.line(left, y, width - left, y)

    def section(label, value, row_y):
        pdf.setFillColorRGB(.42, .42, .42)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(left, row_y, label.upper())
        pdf.setFillColorRGB(.12, .12, .12)
        pdf.setFont("Helvetica", 11)
        pdf.drawString(left, row_y - 18, value)

    y -= 34
    customer_name = booking.customer.get_full_name() or booking.customer.username
    section("Billed to", customer_name, y)
    section("Invoice number", f"TG-{booking.pk:06d}", y - 58)
    y -= 130

    vehicle_description = f"{booking.vehicle_number} | {booking.get_vehicle_type_display()}"
    if booking.car_type:
        vehicle_description += f" | {booking.get_car_type_display()}"
    if booking.vehicle:
        vehicle_description += f" | {booking.vehicle}"
    location_description = ""
    if booking.location_id:
        location_description = (
            f"{booking.location.name}, {booking.location.address}, "
            f"{booking.location.city}, {booking.location.region} {booking.location.postal_code}"
        )
    section("Vehicle", vehicle_description, y)
    section("Garage", location_description or "Location not recorded", y - 58)
    y -= 130

    pdf.setFillColorRGB(.12, .12, .12)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left, y, "SERVICE")
    pdf.drawString(left + 275, y, "APPOINTMENT")
    pdf.drawRightString(width - left, y, "AMOUNT")
    y -= 12
    pdf.setStrokeColorRGB(.82, .82, .82)
    pdf.line(left, y, width - left, y)
    y -= 23
    pdf.setFont("Helvetica", 11)
    pdf.drawString(left, y, booking.service.name)
    pdf.drawString(left + 275, y, f"{booking.appointment_date:%d %b %Y} {booking.appointment_time:%I:%M %p}")
    invoice_total = booking.effective_price
    pdf.drawRightString(width - left, y, f"INR {invoice_total:,.2f}")
    y -= 25
    pdf.setFont("Helvetica", 9)
    pdf.setFillColorRGB(.4, .4, .4)
    pdf.drawString(left, y, f"Booking status: {booking.get_status_display()}")
    y -= 25
    pdf.setStrokeColorRGB(.82, .82, .82)
    pdf.line(left, y, width - left, y)
    y -= 26
    pdf.setFillColorRGB(.12, .12, .12)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(width - left, y, f"TOTAL   INR {invoice_total:,.2f}")
    y -= 26
    if booking.is_paid:
        pdf.setFillColorRGB(.09, .63, .36)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(left, y, "PAYMENT STATUS: PAID IN FULL (UPI ID: 8431699047@nyes)")
        if booking.payment_reference:
            pdf.setFont("Helvetica", 9)
            pdf.drawString(left, y - 14, f"Ref: {booking.payment_reference}")
        if booking.is_vehicle_ready:
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(left, y - 28, "DELIVERY: VEHICLE IS READY TO DELIVER")
    else:
        pdf.setFillColorRGB(.85, .25, .2)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(left, y, "PAYMENT STATUS: DUE (Pay to UPI ID: 8431699047@nyes)")
    pdf.setFillColorRGB(.4, .4, .4)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(left, 54, "Thank you for choosing THE GARAGE.")
    pdf.save()

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="garage-invoice-{booking.pk}.pdf"'
    return response