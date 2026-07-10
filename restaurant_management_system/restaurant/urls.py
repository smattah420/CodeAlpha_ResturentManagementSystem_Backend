"""URL routing configuration for the restaurant application."""

from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import (
    LoginView,
    LogoutView,
    OrderViewSet,
    ReservationViewSet,
    TableViewSet,
    InventoryViewSet,
    MenuItemViewSet,
    api_status_check,
    available_tables_report,
    daily_sales_report,
    low_stock_report,
    monthly_sales_report,
    reserved_tables_report,
    weekly_sales_report,
)

router = DefaultRouter()

router.register(r"tables", TableViewSet, basename="table")
router.register(r"menu-items", MenuItemViewSet, basename="menuitem")
router.register(r"inventory", InventoryViewSet, basename="inventory")
router.register(r"reservations", ReservationViewSet, basename="reservation")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("status/", api_status_check, name="api_status_check"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/token/", obtain_auth_token, name="obtain-auth-token"),
    path("reports/daily-sales/", daily_sales_report, name="daily-sales-report"),
    path("reports/weekly-sales/", weekly_sales_report, name="weekly-sales-report"),
    path("reports/monthly-sales/", monthly_sales_report, name="monthly-sales-report"),
    path("reports/low-stock/", low_stock_report, name="low-stock-report"),
    path("reports/available-tables/", available_tables_report, name="available-tables-report"),
    path("reports/reserved-tables/", reserved_tables_report, name="reserved-tables-report"),
    path("", include(router.urls)),
]
