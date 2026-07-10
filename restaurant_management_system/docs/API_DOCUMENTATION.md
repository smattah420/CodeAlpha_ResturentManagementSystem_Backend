# Restaurant Management System API Documentation

## Base URL
- Development server: http://127.0.0.1:8000/api

## Authentication
The API supports Django session authentication, basic authentication, and token authentication.

### Login
- Method: POST
- Endpoint: /auth/login/
- Body:
  - username
  - password
- Response: returns a user object and a DRF token.

### Logout
- Method: POST
- Endpoint: /auth/logout/
- Headers: Authorization: Token <token>

### Token Auth
- Method: POST
- Endpoint: /auth/token/
- Body:
  - username
  - password

## Resource Endpoints
- GET/POST /tables/
- GET/POST /menu-items/
- GET/POST /inventory/
- GET/POST /reservations/
- GET/POST /orders/

## Report Endpoints
- GET /reports/daily-sales/?date=YYYY-MM-DD
- GET /reports/weekly-sales/?date=YYYY-MM-DD
- GET /reports/monthly-sales/?date=YYYY-MM-DD
- GET /reports/low-stock/
- GET /reports/available-tables/
- GET /reports/reserved-tables/

## Sample Payloads
See the JSON examples in the docs/examples folder.

## Notes
- Read-only requests are public.
- Writes require authentication.
- The API uses standard DRF pagination for list endpoints.
