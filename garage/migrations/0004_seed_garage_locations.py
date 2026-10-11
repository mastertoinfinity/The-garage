from django.db import migrations


LOCATIONS = [
    {"name": "Central Portland", "address": "1842 Harbor Street", "city": "Portland", "region": "OR", "postal_code": "97209", "latitude": "45.528600", "longitude": "-122.681300", "phone": "+15550148200", "sort_order": 1},
    {"name": "Eastside Portland", "address": "1020 SE Belmont Street", "city": "Portland", "region": "OR", "postal_code": "97214", "latitude": "45.516500", "longitude": "-122.654400", "phone": "+15550148200", "sort_order": 2},
    {"name": "Beaverton", "address": "12700 SW Canyon Road", "city": "Beaverton", "region": "OR", "postal_code": "97005", "latitude": "45.487100", "longitude": "-122.805400", "phone": "+15550148200", "sort_order": 3},
]


def seed_locations(apps, schema_editor):
    GarageLocation = apps.get_model("garage", "GarageLocation")
    for location in LOCATIONS:
        GarageLocation.objects.get_or_create(name=location["name"], defaults=location)


def remove_locations(apps, schema_editor):
    GarageLocation = apps.get_model("garage", "GarageLocation")
    GarageLocation.objects.filter(name__in=[location["name"] for location in LOCATIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [("garage", "0003_garagelocation")]
    operations = [migrations.RunPython(seed_locations, remove_locations)]