"""Serializers for the restaurant application."""

from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

from .models import Inventory, MenuItem, Order, OrderItem, Reservation, Table
from .services import (
    check_table_double_booking,
    create_order_with_inventory,
    create_reservation,
    update_order_with_inventory,
    validate_reservation_datetime,
)


class TableSerializer(serializers.ModelSerializer):
    """Validate table properties before they are saved."""

    class Meta:
        model = Table
        fields = ["id", "table_number", "capacity", "status"]

    def validate_table_number(self, value):
        """Ensure the table number is a positive integer."""
        if value <= 0:
            raise serializers.ValidationError("Table number must be a positive integer.")
        return value

    def validate_capacity(self, value):
        """Ensure the capacity is greater than zero."""
        if value <= 0:
            raise serializers.ValidationError("Capacity must be at least 1 seat.")
        return value


class MenuItemSerializer(serializers.ModelSerializer):
    """Validate menu item price values."""

    class Meta:
        model = MenuItem
        fields = ["id", "name", "description", "category", "price", "available"]

    def validate_price(self, value):
        """Verify the price is a positive decimal value."""
        if value <= 0:
            raise serializers.ValidationError("Price must be a positive number greater than 0.")
        return value


class InventorySerializer(serializers.ModelSerializer):
    """Serialize inventory records and include nested menu item details."""

    menu_item_details = MenuItemSerializer(source="menu_item", read_only=True)

    class Meta:
        model = Inventory
        fields = ["id", "menu_item", "menu_item_details", "quantity", "minimum_stock"]


class ReservationSerializer(serializers.ModelSerializer):
    """Validate reservation data and delegate creation to the service layer."""

    class Meta:
        model = Reservation
        fields = [
            "id",
            "customer_name",
            "customer_phone",
            "table",
            "reservation_date",
            "reservation_time",
            "number_of_people",
            "status",
        ]

    def validate_reservation_date(self, value):
        """Ensure reservations are not booked for past dates."""
        if value < timezone.localdate():
            raise serializers.ValidationError("Reservation date cannot be in the past.")
        return value

    def validate(self, data):
        """Apply cross-field validation for capacity, time, and overlap rules."""
        table = data.get("table")
        reservation_date = data.get("reservation_date")
        reservation_time = data.get("reservation_time")
        number_of_people = data.get("number_of_people")

        if table is not None and number_of_people is not None and number_of_people > table.capacity:
            raise serializers.ValidationError(
                {
                    "number_of_people": (
                        f"Number of people ({number_of_people}) exceeds the selected Table capacity ({table.capacity})."
                    )
                }
            )

        if reservation_date is not None and reservation_time is not None:
            try:
                validate_reservation_datetime(reservation_date, reservation_time)
            except ValidationError as exc:
                raise serializers.ValidationError(detail=exc.message) from exc

        if table is not None and reservation_date is not None and reservation_time is not None:
            try:
                exclude_id = self.instance.id if self.instance else None
                check_table_double_booking(
                    table,
                    reservation_date,
                    reservation_time,
                    exclude_reservation_id=exclude_id,
                )
            except ValidationError as exc:
                raise serializers.ValidationError(detail=exc.message) from exc

        return data

    def create(self, validated_data):
        """Delegate reservation creation to the service layer."""
        try:
            return create_reservation(**validated_data)
        except ValidationError as exc:
            raise serializers.ValidationError(detail=exc.message) from exc


class OrderItemSerializer(serializers.ModelSerializer):
    """Serialize individual items in an order."""

    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)
    menu_item_price = serializers.DecimalField(
        source="menu_item.price",
        max_digits=8,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = ["id", "menu_item", "menu_item_name", "menu_item_price", "quantity", "subtotal"]
        read_only_fields = ["subtotal"]


class OrderSerializer(serializers.ModelSerializer):
    """Serialize orders and support nested item writes."""

    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "table", "total_amount", "status", "created_at", "items"]
        read_only_fields = ["total_amount", "created_at"]

    def validate_items(self, value):
        """Verify that an order contains at least one item."""
        if not value:
            raise serializers.ValidationError("An order must contain at least one menu item.")
        return value

    def create(self, validated_data):
        """Create an order and deduct inventory stock."""
        items_data = validated_data.pop("items")
        table = validated_data.get("table")
        status = validated_data.get("status", Order.OrderStatus.PENDING)

        try:
            return create_order_with_inventory(table=table, status=status, items_data=items_data)
        except ValidationError as exc:
            raise serializers.ValidationError(detail=exc.message) from exc

    def update(self, instance, validated_data):
        """Update an order and reconcile inventory stock."""
        items_data = validated_data.pop("items", None)
        table = validated_data.get("table", instance.table)
        status = validated_data.get("status", instance.status)

        try:
            return update_order_with_inventory(
                order=instance,
                table=table,
                status=status,
                items_data=items_data,
            )
        except ValidationError as exc:
            raise serializers.ValidationError(detail=exc.message) from exc

