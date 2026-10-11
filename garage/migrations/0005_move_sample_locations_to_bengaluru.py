from django.db import migrations


LOCATIONS = [
    {
        "old_name": "Central Portland",
        "name": "Indiranagar",
        "address": "100 Feet Road, Indiranagar",
        "city": "Bengaluru",
        "region": "KA",
        "postal_code": "560038",
        "latitude": "12.978400",
        "longitude": "77.640800",
        "phone": "+918040008200",
        "sort_order": 1,
    },
    {
        "old_name": "Eastside Portland",
        "name": "Koramangala",
        "address": "80 Feet Road, 4th Block, Koramangala",
        "city": "Bengaluru",
        "region": "KA",
        "postal_code": "560095",
        "latitude": "12.935200",
        "longitude": "77.624500",
        "phone": "+918040008200",
        "sort_order": 2,
    },
    {
        "old_name": "Beaverton",
        "name": "Whitefield",
        "address": "ITPL Main Road, Whitefield",
        "city": "Bengaluru",
        "region": "KA",
        "postal_code": "560066",
        "latitude": "12.969800",
        "longitude": "77.750000",
        "phone": "+918040008200",
        "sort_order": 3,
    },
]


def move_locations_to_bengaluru(apps, schema_editor):
    GarageLocation = apps.get_model("garage", "GarageLocation")
    for location in LOCATIONS:
        GarageLocation.objects.filter(name=location["old_name"]).update(
            **{key: value for key, value in location.items() if key != "old_name"}
        )


def move_locations_back_to_portland(apps, schema_editor):
    GarageLocation = apps.get_model("garage", "GarageLocation")
    old_locations = [
        ("Central Portland", "1842 Harbor Street", "Portland", "OR", "97209", "45.528600", "-122.681300", 1),
        ("Eastside Portland", "1020 SE Belmont Street", "Portland", "OR", "97214", "45.516500", "-122.654400", 2),
        ("Beaverton", "12700 SW Canyon Road", "Beaverton", "OR", "97005", "45.487100", "-122.805400", 3),
    ]
    for location, old_values in zip(LOCATIONS, old_locations):
        old_name, address, city, region, postal_code, latitude, longitude, sort_order = old_values
        GarageLocation.objects.filter(name=location["name"]).update(
            name=old_name,
            address=address,
            city=city,
            region=region,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude,
            phone="+15550148200",
            sort_order=sort_order,
        )


class Migration(migrations.Migration):
    dependencies = [("garage", "0004_seed_garage_locations")]
    operations = [migrations.RunPython(move_locations_to_bengaluru, move_locations_back_to_portland)]