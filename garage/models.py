from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=180)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    icon = models.CharField(max_length=24, default="wrench")
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Booking(models.Model):
    class VehicleType(models.TextChoices):
        BIKE = "bike", "Bike"
        CAR = "car", "Car"

    class CarType(models.TextChoices):
        SEDAN = "sedan", "Sedan"
        SUV = "suv", "SUV"
        HATCHBACK = "hatchback", "Hatchback"
        MUV = "muv", "MUV"
        ELECTRIC = "electric", "Electric vehicle"
        MINI_SUV = "mini_suv", "Mini SUV"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending confirmation"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        DECLINED = "declined", "Declined"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="bookings")
    location = models.ForeignKey("GarageLocation", on_delete=models.PROTECT, related_name="bookings", null=True, blank=True)
    vehicle_number = models.CharField(max_length=20, blank=True)
    vehicle_type = models.CharField(max_length=8, choices=VehicleType.choices, default=VehicleType.CAR)
    car_type = models.CharField(max_length=16, choices=CarType.choices, blank=True)
    vehicle = models.CharField(max_length=120)
    final_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    invoice_ready = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.CharField(max_length=64, blank=True)
    payment_pending_verification = models.BooleanField(default=False)
    is_ready_for_delivery = models.BooleanField(default=False)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-appointment_date", "-appointment_time"]

    def clean(self):
        errors = {}
        if self.pk is None:
            if not self.vehicle_number.strip():
                errors["vehicle_number"] = "Enter your vehicle registration number."
            if not self.location_id:
                errors["location"] = "Choose the garage location for your appointment."
            if self.vehicle_type == self.VehicleType.CAR and not self.car_type:
                errors["car_type"] = "Choose your car type."
            if self.vehicle_type == self.VehicleType.BIKE and self.car_type:
                errors["car_type"] = "Car type only applies when the vehicle type is car."
        if errors:
            raise ValidationError(errors)
        if self.appointment_date and self.appointment_date < timezone.localdate():
            raise ValidationError({"appointment_date": "Choose today or a future date."})
        if self.appointment_date == timezone.localdate() and self.appointment_time:
            if self.appointment_time <= timezone.localtime().time().replace(second=0, microsecond=0):
                raise ValidationError({"appointment_time": "Choose a time later today."})

    @property
    def is_upcoming(self):
        return self.status in (self.Status.PENDING, self.Status.CONFIRMED) and self.appointment_date >= timezone.localdate()

    @property
    def has_invoice(self):
        return self.invoice_ready or self.status == self.Status.COMPLETED or self.final_price is not None

    @property
    def effective_price(self):
        return self.final_price if self.final_price is not None else self.service.price

    @property
    def is_vehicle_ready(self):
        return self.is_paid and self.is_ready_for_delivery

    @property
    def upi_payment_url(self):
        amount_str = f"{self.effective_price:.2f}"
        return (
            f"upi://pay?pa=8431699047@nyes"
            f"&pn=SUJAN%20C%20R"
            f"&am={amount_str}"
            f"&cu=INR"
            f"&tn=Invoice%20TG-{self.pk:06d}%20THE%20GARAGE"
        )

    def __str__(self):
        return f"{self.service} for {self.customer} on {self.appointment_date}"


class Review(models.Model):
    customer_name = models.CharField(max_length=80)
    vehicle = models.CharField(max_length=100, blank=True)
    rating = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
    body = models.TextField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer_name} ({self.rating}/5)"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=140)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} from {self.name}"


class GarageLocation(models.Model):
    manager = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_garage",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=180)
    city = models.CharField(max_length=80)
    region = models.CharField(max_length=40, default="OR")
    postal_code = models.CharField(max_length=12)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    phone = models.CharField(max_length=30, blank=True)
    hours = models.CharField(max_length=140, default="Mon-Fri 7:30 am-6 pm · Sat 8 am-3 pm")
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.name} - {self.city}"