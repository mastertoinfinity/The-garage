from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Booking, ContactMessage, GarageLocation, Service


class GarageWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="driver", password="long-secure-password")
        self.service = Service.objects.create(
            name="Oil service", slug="oil-service", summary="Fresh oil.",
            description="Oil and filter change.", price="89.00", duration_minutes=45,
        )
        self.location = GarageLocation.objects.create(
            name="Booking Test Branch", address="100 Feet Road", city="Bengaluru",
            region="KA", postal_code="560038", latitude="12.978400", longitude="77.640800",
        )

    def test_home_and_service_catalog_render(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        response = self.client.get(reverse("services"))
        self.assertContains(response, "Oil service")

    def test_booking_requires_login(self):
        response = self.client.get(reverse("book_service"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_staff_can_log_in_to_central_management_dashboard(self):
        staff = User.objects.create_user(username="central-admin", password="long-secure-password", is_staff=True)
        response = self.client.post(reverse("management_login"), {
            "username": staff.username,
            "password": "long-secure-password",
        })
        self.assertRedirects(response, reverse("management_dashboard"))
        dashboard = self.client.get(reverse("management_dashboard"))
        self.assertContains(dashboard, "ADMIN")
        self.assertContains(dashboard, "DASHBOARD")
        self.assertContains(dashboard, "Booking Test Branch")

    def test_regular_customer_cannot_open_management_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("management_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_accept_and_decline_booking_from_management_dashboard(self):
        staff = User.objects.create_user(username="lead-admin", password="long-secure-password", is_staff=True)
        booking = Booking.objects.create(
            customer=self.user, service=self.service, location=self.location,
            vehicle_number="KA 01 AB 9999", vehicle_type=Booking.VehicleType.CAR,
            car_type=Booking.CarType.SEDAN, appointment_date=date.today() + timedelta(days=2),
            appointment_time=time(10, 0),
        )
        self.client.login(username="lead-admin", password="long-secure-password")
        dashboard = self.client.get(reverse("management_dashboard"))
        self.assertContains(dashboard, "Accept")
        self.assertContains(dashboard, "Decline")

        # Accept booking
        accept = self.client.post(reverse("management_booking_action", args=[booking.pk]), {"action": "accept"})
        self.assertRedirects(accept, reverse("management_dashboard"))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

        # Non-staff cannot perform action
        self.client.logout()
        self.client.login(username="driver", password="long-secure-password")
        forbidden = self.client.post(reverse("management_booking_action", args=[booking.pk]), {"action": "accept"})
        self.assertEqual(forbidden.status_code, 403)

    def test_branch_assigned_staff_is_sent_to_branch_desk(self):
        manager = User.objects.create_user(username="assigned-manager", password="long-secure-password", is_staff=True)
        self.location.manager = manager
        self.location.save(update_fields=["manager"])
        response = self.client.post(reverse("management_login"), {
            "username": manager.username,
            "password": "long-secure-password",
        })
        self.assertRedirects(response, reverse("branch_dashboard"))

    def test_booking_form_lists_vehicle_types_car_styles_and_branches(self):
        self.client.login(username="driver", password="long-secure-password")
        response = self.client.get(reverse("book_service"))
        for label in ("Bike", "Car", "Sedan", "SUV", "Hatchback", "MUV", "Electric vehicle", "Mini SUV", "Booking Test Branch"):
            self.assertContains(response, label)

    def test_customer_can_create_future_booking(self):
        self.client.login(username="driver", password="long-secure-password")
        response = self.client.post(reverse("book_service"), {
            "service": self.service.pk,
            "location": self.location.pk,
            "vehicle_number": "ka 01 ab 1234",
            "vehicle_type": Booking.VehicleType.BIKE,
            "car_type": "",
            "vehicle": "2021 Toyota Corolla",
            "appointment_date": (date.today() + timedelta(days=2)).isoformat(),
            "appointment_time": "10:30",
            "notes": "Please check the tires too.",
        })
        self.assertRedirects(response, reverse("booking_history"))
        booking = Booking.objects.get(customer=self.user)
        self.assertEqual(booking.service, self.service)
        self.assertEqual(booking.location, self.location)
        self.assertEqual(booking.vehicle_number, "KA 01 AB 1234")
        self.assertEqual(booking.vehicle_type, Booking.VehicleType.BIKE)
        self.assertEqual(booking.status, Booking.Status.PENDING)

    def test_past_booking_date_is_rejected(self):
        self.client.login(username="driver", password="long-secure-password")
        response = self.client.post(reverse("book_service"), {
            "service": self.service.pk,
            "location": self.location.pk,
            "vehicle_number": "KA 01 AB 1234",
            "vehicle_type": Booking.VehicleType.CAR,
            "car_type": Booking.CarType.SEDAN,
            "vehicle": "2021 Toyota Corolla",
            "appointment_date": (date.today() - timedelta(days=1)).isoformat(),
            "appointment_time": "10:30",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.exists())

    def test_car_booking_requires_a_car_type(self):
        self.client.login(username="driver", password="long-secure-password")
        response = self.client.post(reverse("book_service"), {
            "service": self.service.pk,
            "location": self.location.pk,
            "vehicle_number": "KA 01 AB 1234",
            "vehicle_type": Booking.VehicleType.CAR,
            "car_type": "",
            "vehicle": "2022 Electric car",
            "appointment_date": (date.today() + timedelta(days=2)).isoformat(),
            "appointment_time": "10:30",
        })
        self.assertContains(response, "Choose your car type.")
        self.assertFalse(Booking.objects.exists())

    def test_customer_can_create_car_booking_with_body_type(self):
        self.client.login(username="driver", password="long-secure-password")
        response = self.client.post(reverse("book_service"), {
            "service": self.service.pk,
            "location": self.location.pk,
            "vehicle_number": "KA 03 CD 5678",
            "vehicle_type": Booking.VehicleType.CAR,
            "car_type": Booking.CarType.ELECTRIC,
            "vehicle": "2024 electric hatchback",
            "appointment_date": (date.today() + timedelta(days=3)).isoformat(),
            "appointment_time": "11:00",
        })
        self.assertRedirects(response, reverse("booking_history"))
        booking = Booking.objects.get(customer=self.user)
        self.assertEqual(booking.vehicle_type, Booking.VehicleType.CAR)
        self.assertEqual(booking.car_type, Booking.CarType.ELECTRIC)
        self.assertEqual(booking.location, self.location)

    def test_customer_can_view_and_download_own_invoice(self):
        booking = Booking.objects.create(
            customer=self.user,
            service=self.service,
            location=self.location,
            vehicle_number="KA 03 CD 5678",
            vehicle_type=Booking.VehicleType.CAR,
            car_type=Booking.CarType.SEDAN,
            vehicle="2021 Toyota Corolla",
            appointment_date=date.today() - timedelta(days=2),
            appointment_time=time(10, 30),
            status=Booking.Status.COMPLETED,
        )
        self.client.login(username="driver", password="long-secure-password")

        invoice = self.client.get(reverse("invoice_detail", args=[booking.pk]))
        self.assertContains(invoice, f"TG-{booking.pk:06d}")
        self.assertContains(invoice, "KA 03 CD 5678")
        self.assertContains(invoice, "Booking Test Branch")

        pdf = self.client.get(reverse("invoice_pdf", args=[booking.pk]))
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertIn(f'garage-invoice-{booking.pk}.pdf', pdf["Content-Disposition"])
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_invoice_uses_branch_final_price(self):
        booking = Booking.objects.create(
            customer=self.user,
            service=self.service,
            location=self.location,
            vehicle_number="KA 03 CD 5678",
            vehicle_type=Booking.VehicleType.CAR,
            car_type=Booking.CarType.SEDAN,
            vehicle="2021 Toyota Corolla",
            appointment_date=date.today() - timedelta(days=2),
            appointment_time=time(10, 30),
            status=Booking.Status.COMPLETED,
            final_price="1550.00",
        )
        self.client.login(username="driver", password="long-secure-password")
        response = self.client.get(reverse("invoice_detail", args=[booking.pk]))
        self.assertContains(response, "₹1550.00")

    def test_customer_can_pay_via_upi_and_see_vehicle_ready_for_delivery(self):
        booking = Booking.objects.create(
            customer=self.user,
            service=self.service,
            location=self.location,
            vehicle_number="KA 03 CD 5678",
            vehicle_type=Booking.VehicleType.CAR,
            car_type=Booking.CarType.SEDAN,
            vehicle="2021 Toyota Corolla",
            appointment_date=date.today() - timedelta(days=2),
            appointment_time=time(10, 30),
            status=Booking.Status.CONFIRMED,
            final_price="1550.00",
            invoice_ready=True,
        )
        self.client.login(username="driver", password="long-secure-password")

        invoice = self.client.get(reverse("invoice_detail", args=[booking.pk]))
        self.assertContains(invoice, "8431699047@nyes")
        self.assertContains(invoice, "SUJAN C R")
        self.assertContains(invoice, "upi://pay")

        payment_resp = self.client.post(reverse("pay_booking_upi", args=[booking.pk]), {
            "payment_reference": "UTR1234567890",
        })
        self.assertRedirects(payment_resp, reverse("invoice_detail", args=[booking.pk]))
        booking.refresh_from_db()
        # Payment must remain unverified until admin checks it
        self.assertFalse(booking.is_paid)
        self.assertFalse(booking.is_ready_for_delivery)
        self.assertTrue(booking.payment_pending_verification)
        self.assertEqual(booking.payment_reference, "UTR1234567890")

        # Customer sees verification in progress, NOT ready for delivery yet
        pending_invoice = self.client.get(reverse("invoice_detail", args=[booking.pk]))
        self.assertContains(pending_invoice, "PAYMENT VERIFICATION IN PROGRESS")
        self.assertNotContains(pending_invoice, "YOUR VEHICLE IS READY TO DELIVER!")

        dashboard = self.client.get(reverse("dashboard"))
        self.assertContains(dashboard, "PAYMENT SUBMITTED · AWAITING ADMIN VERIFICATION")
        self.assertNotContains(dashboard, "VEHICLE IS READY TO DELIVER!")

        # Admin logs in and verifies the transaction
        admin_user = User.objects.create_user(username="payment-verifier", password="long-secure-password", is_staff=True)
        self.client.login(username="payment-verifier", password="long-secure-password")
        mgmt_dash = self.client.get(reverse("management_dashboard"))
        self.assertContains(mgmt_dash, "UTR1234567890")
        self.assertContains(mgmt_dash, "verify_payment")

        verify_resp = self.client.post(reverse("management_booking_action", args=[booking.pk]), {
            "action": "verify_payment",
        })
        self.assertRedirects(verify_resp, reverse("management_dashboard"))

        booking.refresh_from_db()
        self.assertTrue(booking.is_paid)
        self.assertTrue(booking.is_ready_for_delivery)
        self.assertFalse(booking.payment_pending_verification)

        # Now customer logs back in and sees the vehicle ready to deliver message
        self.client.login(username="driver", password="long-secure-password")
        paid_invoice = self.client.get(reverse("invoice_detail", args=[booking.pk]))
        self.assertContains(paid_invoice, "YOUR VEHICLE IS READY TO DELIVER!")
        self.assertContains(paid_invoice, "PAID IN FULL")

        history = self.client.get(reverse("booking_history"))
        self.assertContains(history, "Vehicle ready to deliver")

        dashboard = self.client.get(reverse("dashboard"))
        self.assertContains(dashboard, "VEHICLE IS READY TO DELIVER!")

    def test_login_page_has_switch_to_admin_login(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, reverse("management_login"))
        self.assertContains(response, "Switch to Admin Login")

    def test_branch_manager_sees_only_their_own_location_bookings(self):
        manager = User.objects.create_user(username="indiranagar-manager", password="long-secure-password")
        other_manager = User.objects.create_user(username="whitefield-manager", password="long-secure-password")
        other_location = GarageLocation.objects.create(
            name="Other Test Branch", address="ITPL Road", city="Bengaluru", region="KA",
            postal_code="560066", latitude="12.969800", longitude="77.750000", manager=other_manager,
        )
        self.location.manager = manager
        self.location.save(update_fields=["manager"])
        own_booking = Booking.objects.create(
            customer=self.user, service=self.service, location=self.location,
            vehicle_number="KA 01 AA 1111", vehicle_type=Booking.VehicleType.BIKE,
            vehicle="Scooter", appointment_date=date.today() + timedelta(days=2), appointment_time=time(10, 0),
        )
        other_customer = User.objects.create_user(username="other-customer", password="long-secure-password")
        Booking.objects.create(
            customer=other_customer, service=self.service, location=other_location,
            vehicle_number="KA 02 BB 2222", vehicle_type=Booking.VehicleType.CAR,
            car_type=Booking.CarType.SUV, vehicle="SUV", appointment_date=date.today() + timedelta(days=3), appointment_time=time(11, 0),
        )
        self.client.login(username="indiranagar-manager", password="long-secure-password")
        response = self.client.get(reverse("branch_dashboard"))
        self.assertContains(response, "KA 01 AA 1111")
        self.assertNotContains(response, "KA 02 BB 2222")
        self.assertContains(response, "Branch desk")
        self.assertEqual(own_booking.location, self.location)

    def test_branch_manager_accepts_and_completes_own_booking(self):
        manager = User.objects.create_user(username="branch-manager", password="long-secure-password")
        self.location.manager = manager
        self.location.save(update_fields=["manager"])
        booking = Booking.objects.create(
            customer=self.user, service=self.service, location=self.location,
            vehicle_number="KA 01 AA 1111", vehicle_type=Booking.VehicleType.BIKE,
            vehicle="Scooter", appointment_date=date.today() + timedelta(days=2), appointment_time=time(10, 0),
        )
        self.client.login(username="branch-manager", password="long-secure-password")
        accept = self.client.post(reverse("branch_booking_action", args=[booking.pk]), {"action": "accept"})
        self.assertRedirects(accept, reverse("branch_dashboard"))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

        complete = self.client.post(reverse("branch_booking_action", args=[booking.pk]), {
            "action": "complete", "final_price": "1550.00",
        })
        self.assertRedirects(complete, reverse("branch_dashboard"))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.COMPLETED)
        self.assertEqual(booking.final_price, Decimal("1550.00"))

        self.client.logout()
        self.client.login(username="driver", password="long-secure-password")
        invoice = self.client.get(reverse("invoice_detail", args=[booking.pk]))
        self.assertContains(invoice, "₹1550.00")

    def test_branch_manager_cannot_act_on_another_location_booking(self):
        manager = User.objects.create_user(username="branch-manager", password="long-secure-password")
        other_manager = User.objects.create_user(username="other-manager", password="long-secure-password")
        self.location.manager = manager
        self.location.save(update_fields=["manager"])
        other_location = GarageLocation.objects.create(
            name="Other Test Branch", address="ITPL Road", city="Bengaluru", region="KA",
            postal_code="560066", latitude="12.969800", longitude="77.750000", manager=other_manager,
        )
        booking = Booking.objects.create(
            customer=self.user, service=self.service, location=other_location,
            vehicle_number="KA 02 BB 2222", vehicle_type=Booking.VehicleType.CAR,
            car_type=Booking.CarType.SUV, vehicle="SUV", appointment_date=date.today() + timedelta(days=2), appointment_time=time(10, 0),
        )
        self.client.login(username="branch-manager", password="long-secure-password")
        response = self.client.post(reverse("branch_booking_action", args=[booking.pk]), {"action": "accept"})
        self.assertEqual(response.status_code, 404)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.PENDING)

    def test_customer_cannot_view_another_customers_invoice(self):
        other = User.objects.create_user(username="another-driver", password="long-secure-password")
        booking = Booking.objects.create(
            customer=other,
            service=self.service,
            location=self.location,
            vehicle_number="KA 01 ZZ 0099",
            vehicle_type=Booking.VehicleType.BIKE,
            vehicle="2022 scooter",
            appointment_date=date.today() - timedelta(days=1),
            appointment_time=time(11, 0),
        )
        self.client.login(username="driver", password="long-secure-password")
        self.assertEqual(self.client.get(reverse("invoice_detail", args=[booking.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("invoice_pdf", args=[booking.pk])).status_code, 404)

    def test_past_service_history_has_invoice_actions(self):
        booking = Booking.objects.create(
            customer=self.user,
            service=self.service,
            location=self.location,
            vehicle_number="KA 03 CD 5678",
            vehicle_type=Booking.VehicleType.BIKE,
            vehicle="2022 scooter",
            appointment_date=date.today() - timedelta(days=2),
            appointment_time=time(10, 30),
            status=Booking.Status.COMPLETED,
        )
        self.client.login(username="driver", password="long-secure-password")
        response = self.client.get(reverse("booking_history"))
        self.assertContains(response, reverse("invoice_detail", args=[booking.pk]))
        self.assertContains(response, reverse("invoice_pdf", args=[booking.pk]))

    def test_contact_form_stores_message(self):
        response = self.client.post(reverse("contact"), {
            "name": "Casey Driver", "email": "casey@example.com",
            "subject": "Noisy brakes", "message": "Can you take a look this week?",
        })
        self.assertRedirects(response, reverse("contact"))
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_contact_page_lists_active_locations_for_map(self):
        GarageLocation.objects.create(
            name="Active Test Branch", address="1842 Harbor Street", city="Portland",
            postal_code="97209", latitude="45.528600", longitude="-122.681300",
        )
        GarageLocation.objects.create(
            name="Inactive Test Branch", address="1020 SE Belmont Street", city="Portland",
            postal_code="97214", latitude="45.516500", longitude="-122.654400", is_active=False,
        )
        response = self.client.get(reverse("contact"))
        self.assertContains(response, "Active Test Branch")
        self.assertNotContains(response, "Inactive Test Branch")
        self.assertContains(response, "garage-map")

    def test_service_history_is_customer_scoped(self):
        other = User.objects.create_user(username="other", password="long-secure-password")
        Booking.objects.create(customer=other, service=self.service, vehicle="Other vehicle",
                               appointment_date=date.today() + timedelta(days=3), appointment_time=time(10, 0))
        self.client.login(username="driver", password="long-secure-password")
        response = self.client.get(reverse("booking_history"))
        self.assertNotContains(response, "Other vehicle")