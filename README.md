# THE GARAGE

A Django MVT garage management and service-booking website. Customers can browse services and reviews, contact the shop, create an account, request appointments, and see upcoming bookings and their service history. Staff manage the service catalog, reviews, contact messages, and booking statuses through Django admin.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. The development server uses SQLite and the service catalog is loaded by a data migration. The admin is at `/admin/`. The branch map uses MapLibre GL with OpenFreeMap vector tiles and automatic attribution; it does not request tiles from OpenStreetMap's volunteer raster server. The map starts with three sample Bengaluru branches; replace their addresses, phone numbers, and coordinates in **Garage locations** in Django admin before publishing.

## Branch booking workflow

Create one Django user account for each branch manager. In Django admin, assign that user in the branch's **Manager** field under **Garage locations**. Managers sign in through the normal site login and use **Branch desk** to see only bookings for their assigned branch. They can accept or decline pending requests; accepted jobs can be marked complete with the final invoice amount. Customers see and download the final invoice from **My garage → Service history** after completion.

Central staff sign in at `/management/login/` to open the all-branch dashboard at `/management/`. Django's `/admin/` remains available for configuring users, services, branches, and reviews. Branch-assigned managers are redirected to their own branch desk instead of the all-branch dashboard.

## Checks

```powershell
python manage.py check
python manage.py test
```

## Production notes

This project is configured for local development. Before deployment, set a strong `SECRET_KEY` from the environment, disable `DEBUG`, configure `ALLOWED_HOSTS`, serve static files with a production web server, and use a production database. The sample contact details and shop address are demonstration content. Automotive photography and display fonts load from Unsplash and Google Fonts.