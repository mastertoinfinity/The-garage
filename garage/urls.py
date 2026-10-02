from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("healthz/", views.health_check, name="health_check"),
    path("services/", views.services, name="services"),
    path("contact/", views.contact, name="contact"),
    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("management/login/", views.management_login, name="management_login"),
    path("management/", views.management_dashboard, name="management_dashboard"),
    path("management/bookings/<int:booking_id>/action/", views.management_booking_action, name="management_booking_action"),
    path("book/", views.book_service, name="book_service"),
    path("account/", views.dashboard, name="dashboard"),
    path("account/bookings/", views.booking_history, name="booking_history"),
    path("account/bookings/<int:booking_id>/invoice/", views.invoice_detail, name="invoice_detail"),
    path("account/bookings/<int:booking_id>/invoice/download/", views.invoice_pdf, name="invoice_pdf"),
    path("account/bookings/<int:booking_id>/pay/", views.pay_booking_upi, name="pay_booking_upi"),
    path("branch/", views.branch_dashboard, name="branch_dashboard"),
    path("branch/bookings/<int:booking_id>/action/", views.branch_booking_action, name="branch_booking_action"),
]