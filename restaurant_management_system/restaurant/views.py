"""Views for the restaurant application."""

from datetime import date, timedelta

from django.contrib.auth import authenticate, login, logout
from django.db.models import F, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Inventory, MenuItem, Order, Reservation, Table
from .serializers import (
    InventorySerializer,
    MenuItemSerializer,
    OrderSerializer,
    ReservationSerializer,
    TableSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def api_status_check(request):
    """Return a simple health-check payload for the API."""
    return Response(
        {
            "status": "online",
            "message": "Restaurant Management System API is running successfully.",
            "version": "1.0.0",
        },
        status=status.HTTP_200_OK,
    )


class LoginView(APIView):
    """Authenticate a staff user and issue an API token."""

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")

        if not username or not password:
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "detail": "Login successful.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                "token": token.key,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """End the current session and remove the token for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        token = getattr(request, "auth", None)
        if token is None:
            token = getattr(request.user, "auth_token", None)
        if token is not None:
            token.delete()
        return Response({"detail": "Logout successful."}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def daily_sales_report(request):
    """Return the sales summary for a single day."""
    try:
        selected_date = _get_selected_date(request.query_params.get("date"))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    orders = Order.objects.filter(
        status=Order.OrderStatus.PAID,
        created_at__date=selected_date,
    )

    return Response(
        {
            "date": selected_date.isoformat(),
            **_summarize_sales(orders),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def weekly_sales_report(request):
    """Summarize paid orders for the current week."""
    try:
        selected_date = _get_selected_date(request.query_params.get("date"))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    orders = Order.objects.filter(
        status=Order.OrderStatus.PAID,
        created_at__date__range=(start_of_week, end_of_week),
    )

    return Response(
        {
            "start_date": start_of_week.isoformat(),
            "end_date": end_of_week.isoformat(),
            **_summarize_sales(orders),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def monthly_sales_report(request):
    """Summarize monthly sales for revenue review."""
    try:
        selected_date = _get_selected_date(request.query_params.get("date"))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    orders = Order.objects.filter(
        status=Order.OrderStatus.PAID,
        created_at__year=selected_date.year,
        created_at__month=selected_date.month,
    )

    return Response(
        {
            "year": selected_date.year,
            "month": selected_date.month,
            **_summarize_sales(orders),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def low_stock_report(request):
    """List menu items that are at or below their minimum stock threshold."""
    inventory_items = (
        Inventory.objects.select_related("menu_item")
        .filter(quantity__lte=F("minimum_stock"))
        .order_by("quantity", "minimum_stock")
    )

    payload = [
        {
            "menu_item": {
                "id": item.menu_item.id,
                "name": item.menu_item.name,
                "category": item.menu_item.category,
            },
            "quantity": item.quantity,
            "minimum_stock": item.minimum_stock,
            "is_low_stock": item.quantity <= item.minimum_stock,
        }
        for item in inventory_items
    ]

    return Response(payload, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def available_tables_report(request):
    """Return every dining table that is currently available for new guests."""
    tables = Table.objects.filter(status=Table.TableStatus.AVAILABLE).order_by("table_number")
    return Response(_serialize_tables(tables), status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def reserved_tables_report(request):
    """Return every dining table that is currently marked as reserved."""
    tables = Table.objects.filter(status=Table.TableStatus.RESERVED).order_by("table_number")
    return Response(_serialize_tables(tables), status=status.HTTP_200_OK)


def _serialize_tables(tables):
    """Build a consistent JSON payload for table reports."""
    return [
        {
            "id": table.id,
            "table_number": table.table_number,
            "capacity": table.capacity,
            "status": table.status,
        }
        for table in tables
    ]


def _summarize_sales(orders):
    """Create a shared response block for sales reports."""
    total_sales = orders.aggregate(total_sales=Sum("total_amount"))["total_sales"] or 0
    return {
        "order_count": orders.count(),
        "total_sales": total_sales,
    }


def _get_selected_date(value):
    """Normalize report dates from query parameters to a real date object."""
    if value:
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Date must be provided in YYYY-MM-DD format.") from exc
    return timezone.localdate()


class TableViewSet(viewsets.ModelViewSet):
    """Handle CRUD operations for dining tables."""

    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class MenuItemViewSet(viewsets.ModelViewSet):
    """Handle CRUD operations for menu items."""

    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class InventoryViewSet(viewsets.ModelViewSet):
    """Track inventory levels."""

    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ReservationViewSet(viewsets.ModelViewSet):
    """Handle table reservations."""

    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class OrderViewSet(viewsets.ModelViewSet):
    """Manage customer orders and their nested items."""

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
