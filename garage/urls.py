from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("services/", views.services, name="services"),
    path("contact/", views.contact, name="contact"),
    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("book/", views.book_service, name="book_service"),
    path("account/", views.dashboard, name="dashboard"),
    path("account/bookings/", views.booking_history, name="booking_history"),
]