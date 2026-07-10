# Restaurant Management System Backend

This project is a Django REST Framework backend for a restaurant management workflow. It includes table management, menu items, inventory tracking, reservations, orders, authentication, an enhanced Django admin panel, and reporting APIs.

## Features
- Django authentication and token-based API access
- Admin panel with search, filters, and list display customization
- REST APIs for tables, menu items, inventory, reservations, and orders
- Business reports for daily, weekly, monthly, low-stock, available-table, and reserved-table views
- Clean, tested, and documented backend structure for internships and portfolio use

## Installation
### 1. Prerequisites
- Python 3.10+ recommended
- Windows PowerShell or a similar terminal

### 2. Create and activate a virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Apply database migrations
```powershell
python manage.py migrate
```

### 5. Create an admin user
```powershell
python manage.py createsuperuser
```

## Running the Server
```powershell
python manage.py runserver
```

Open the app at:
- API status: http://127.0.0.1:8000/api/status/
- Admin panel: http://127.0.0.1:8000/admin/

## API List
### Authentication
- POST /api/auth/login/
- POST /api/auth/logout/
- POST /api/auth/token/

### Resources
- GET/POST /api/tables/
- GET/POST /api/menu-items/
- GET/POST /api/inventory/
- GET/POST /api/reservations/
- GET/POST /api/orders/

### Reports
- GET /api/reports/daily-sales/?date=YYYY-MM-DD
- GET /api/reports/weekly-sales/?date=YYYY-MM-DD
- GET /api/reports/monthly-sales/?date=YYYY-MM-DD
- GET /api/reports/low-stock/
- GET /api/reports/available-tables/
- GET /api/reports/reserved-tables/

## Testing Guide
Run the full test suite:
```powershell
python manage.py test
```

The project includes automated tests for:
- API health checks
- CRUD flows for core resources
- Authentication and token behavior
- Sales and stock reporting endpoints

## Project Structure
- [restaurant/](restaurant/): app logic, models, serializers, views, tests, and admin configuration
- [restaurant_management_system/](restaurant_management_system/): Django project settings and URL configuration
- [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md): endpoint documentation
- [docs/postman/restaurant-management-system.postman_collection.json](docs/postman/restaurant-management-system.postman_collection.json): Postman collection
- [docs/examples/](docs/examples/): sample request and response JSON files
- [docs/screenshots/](docs/screenshots/): screenshot placeholders for portfolio presentation

## Documentation and Samples
- API docs: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)
- Postman collection: [docs/postman/restaurant-management-system.postman_collection.json](docs/postman/restaurant-management-system.postman_collection.json)
- Sample payloads: [docs/examples/](docs/examples/)


