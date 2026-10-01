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

Open `http://127.0.0.1:8000/`. The development server uses SQLite and the service catalog is loaded by a data migration. The admin is at `/admin/`.

## Checks

```powershell
python manage.py check
python manage.py test
```

## Production notes

This project is configured for local development. Before deployment, set a strong `SECRET_KEY` from the environment, disable `DEBUG`, configure `ALLOWED_HOSTS`, serve static files with a production web server, and use a production database. The sample contact details and shop address are demonstration content. Automotive photography and display fonts load from Unsplash and Google Fonts.