from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Booking, ContactMessage, Service


class GarageWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="driver", password="long-secure-password")
        self.service = Service.objects.create(
            name="Oil service", slug="oil-service", summary="Fresh oil.",
            description="Oil and filter change.", price="89.00", duration_minutes=45,
        )

    def test_home_and_service_catalog_render(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        response = self.client.get(reverse("services"))
        self.assertContains(response, "Oil service")

    def test_booking_requires_login(self):
        response = self.client.get(reverse("book_service"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_customer_can_create_future_booking(self):
        self.client.login(username="driver", password="long-secure-password")
        response = self.client.post(reverse("book_service"), {
            "service": self.service.pk,
            "vehicle": "2021 Toyota Corolla",
            "appointment_date": (date.today() + timedelta(days=2)).isoformat(),
            "appointment_time": "10:30",
            "notes": "Please check the tires too.",
        })
        self.assertRedirects(response, reverse("booking_history"))
        booking = Booking.objects.get(customer=self.user)
        self.assertEqual(booking.service, self.service)
        self.assertEqual(booking.status, Booking.Status.PENDING)

    def test_past_booking_date_is_rejected(self):
        self.client.login(username="driver", password="long-secure-password")
        response = self.client.post(reverse("book_service"), {
            "service": self.service.pk,
            "vehicle": "2021 Toyota Corolla",
            "appointment_date": (date.today() - timedelta(days=1)).isoformat(),
            "appointment_time": "10:30",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.exists())

    def test_contact_form_stores_message(self):
        response = self.client.post(reverse("contact"), {
            "name": "Casey Driver", "email": "casey@example.com",
            "subject": "Noisy brakes", "message": "Can you take a look this week?",
        })
        self.assertRedirects(response, reverse("contact"))
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_service_history_is_customer_scoped(self):
        other = User.objects.create_user(username="other", password="long-secure-password")
        Booking.objects.create(customer=other, service=self.service, vehicle="Other vehicle",
                               appointment_date=date.today() + timedelta(days=3), appointment_time=time(10, 0))
        self.client.login(username="driver", password="long-secure-password")
        response = self.client.get(reverse("booking_history"))
        self.assertNotContains(response, "Other vehicle")