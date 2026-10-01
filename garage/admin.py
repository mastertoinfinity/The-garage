from django.contrib import admin

from .models import Booking, ContactMessage, Review, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration_minutes", "is_active", "is_featured")
    list_filter = ("is_active", "is_featured")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("customer", "service", "vehicle", "appointment_date", "appointment_time", "status")
    list_filter = ("status", "appointment_date", "service")
    search_fields = ("customer__username", "vehicle")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "rating", "is_published", "created_at")
    list_filter = ("rating", "is_published")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "subject")