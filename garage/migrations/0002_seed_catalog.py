from django.db import migrations


SERVICES = [
    ("Precision oil service", "precision-oil-service", "Fresh oil. Longer engine life.", "Premium synthetic oil, a genuine filter, fluid top-offs and a multi-point inspection.", "89.00", 45, "oil", True),
    ("Brake inspection & repair", "brake-inspection-repair", "Confidence starts with a clean stop.", "A complete brake system inspection with clear recommendations and quality replacement parts.", "129.00", 90, "brake", True),
    ("Diagnostics & repair", "diagnostics-repair", "Find the issue. Fix it right.", "Advanced computer diagnostics and hands-on troubleshooting from experienced technicians.", "115.00", 75, "scan", True),
    ("Tire & wheel service", "tire-wheel-service", "Grip, balance and a smoother ride.", "Tire rotation, pressure check and wheel balancing to keep your drive feeling right.", "69.00", 60, "tire", False),
    ("Battery & electrical", "battery-electrical", "Reliable starts, every time.", "Battery health testing, replacement and charging system inspection.", "79.00", 45, "battery", False),
    ("Full vehicle inspection", "full-vehicle-inspection", "Know your car inside out.", "A detailed inspection of key safety, fluid and mechanical systems with a plain-English report.", "99.00", 60, "inspect", False),
]


def seed_services(apps, schema_editor):
    Service = apps.get_model("garage", "Service")
    for name, slug, summary, description, price, duration, icon, featured in SERVICES:
        Service.objects.get_or_create(slug=slug, defaults={"name": name, "summary": summary, "description": description, "price": price, "duration_minutes": duration, "icon": icon, "is_featured": featured})


def remove_services(apps, schema_editor):
    apps.get_model("garage", "Service").objects.filter(slug__in=[item[1] for item in SERVICES]).delete()


class Migration(migrations.Migration):
    dependencies = [("garage", "0001_initial")]
    operations = [migrations.RunPython(seed_services, remove_services)]