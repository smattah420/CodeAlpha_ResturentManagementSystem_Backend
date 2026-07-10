"""Service layer for the restaurant application."""

from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Inventory, Order, OrderItem, Reservation, Table


def validate_reservation_datetime(reservation_date, reservation_time):
    """Validate that a reservation is booked for a future date and time."""
    today = timezone.localdate()
    now_time = timezone.localtime().time()

    if reservation_date < today:
        raise ValidationError("Reservation date cannot be in the past.")

    if reservation_date == today and reservation_time < now_time:
        raise ValidationError("Reservation time cannot be in the past today.")


def check_table_double_booking(table, reservation_date, reservation_time, exclude_reservation_id=None):
    """Ensure a table is not double-booked within a two-hour window."""
    requested_start = datetime.combine(reservation_date, reservation_time)
    buffer = timedelta(hours=2)
    requested_end = requested_start + buffer

    existing_reservations = Reservation.objects.filter(
        table=table,
        reservation_date=reservation_date,
    ).exclude(status=Reservation.ReservationStatus.CANCELLED)

    if exclude_reservation_id:
        existing_reservations = existing_reservations.exclude(id=exclude_reservation_id)

    for existing_reservation in existing_reservations:
        existing_start = datetime.combine(existing_reservation.reservation_date, existing_reservation.reservation_time)
        existing_end = existing_start + buffer
        if requested_start < existing_end and requested_end > existing_start:
            raise ValidationError(
                f"Table {table.table_number} is already booked from "
                f"{existing_reservation.reservation_time.strftime('%H:%M')} to {existing_end.time().strftime('%H:%M')} on this date."
            )


@transaction.atomic
def create_reservation(
    customer_name,
    customer_phone,
    table,
    reservation_date,
    reservation_time,
    number_of_people,
    status=Reservation.ReservationStatus.PENDING,
):
    """Create a reservation after validating capacity, time, and overlap rules."""
    if number_of_people > table.capacity:
        raise ValidationError(
            f"Number of people ({number_of_people}) exceeds table capacity ({table.capacity})."
        )

    validate_reservation_datetime(reservation_date, reservation_time)
    check_table_double_booking(table, reservation_date, reservation_time)

    today = timezone.localdate()
    if reservation_date == today and table.status == Table.TableStatus.OCCUPIED:
        raise ValidationError("This table is currently occupied by active diners.")

    reservation = Reservation.objects.create(
        customer_name=customer_name,
        customer_phone=customer_phone,
        table=table,
        reservation_date=reservation_date,
        reservation_time=reservation_time,
        number_of_people=number_of_people,
        status=status,
    )

    if reservation_date == today and status == Reservation.ReservationStatus.CONFIRMED:
        table.status = Table.TableStatus.RESERVED
        table.save()

    return reservation


def _get_inventory_record(menu_item):
    return Inventory.objects.filter(menu_item=menu_item).first()


def check_stock_sufficiency(items_data):
    """Verify that the requested items are in stock."""
    item_totals = {}
    for item in items_data:
        menu_item = item["menu_item"]
        quantity = item["quantity"]
        item_totals[menu_item] = item_totals.get(menu_item, 0) + quantity

    for menu_item, requested_quantity in item_totals.items():
        inventory_record = _get_inventory_record(menu_item)
        available_quantity = inventory_record.quantity if inventory_record else 0

        if available_quantity < requested_quantity:
            raise ValidationError(
                f"Insufficient inventory for item '{menu_item.name}'. "
                f"Available stock: {available_quantity}, Requested: {requested_quantity}."
            )


def deduct_inventory_stock(items_data):
    """Deduct stock for each ordered menu item."""
    for item in items_data:
        inventory_record = _get_inventory_record(item["menu_item"])
        if inventory_record:
            inventory_record.quantity -= item["quantity"]
            inventory_record.save()


def restore_inventory_stock(items_data):
    """Restore stock levels for items that are removed or cancelled."""
    for item in items_data:
        inventory_record = _get_inventory_record(item["menu_item"])
        if inventory_record:
            inventory_record.quantity += item["quantity"]
            inventory_record.save()


@transaction.atomic
def create_order_with_inventory(table, status, items_data):
    """Validate stock, deduct inventory, and create an order with nested items."""
    check_stock_sufficiency(items_data)
    deduct_inventory_stock(items_data)

    order = Order.objects.create(table=table, status=status)

    for item in items_data:
        OrderItem.objects.create(
            order=order,
            menu_item=item["menu_item"],
            quantity=item["quantity"],
        )

    order.update_total_amount()

    if table and status not in {Order.OrderStatus.PAID, Order.OrderStatus.CANCELLED}:
        table.status = Table.TableStatus.OCCUPIED
        table.save()

    return order


@transaction.atomic
def update_order_with_inventory(order, table, status, items_data=None):
    """Update order fields and reconcile inventory stock."""
    if items_data is not None:
        old_items = [{"menu_item": item.menu_item, "quantity": item.quantity} for item in order.items.all()]

        restore_inventory_stock(old_items)

        try:
            check_stock_sufficiency(items_data)
        except ValidationError:
            deduct_inventory_stock(old_items)
            raise

        deduct_inventory_stock(items_data)

        order.items.all().delete()

        for item in items_data:
            OrderItem.objects.create(
                order=order,
                menu_item=item["menu_item"],
                quantity=item["quantity"],
            )

    order.table = table
    order.status = status
    order.save()

    order.update_total_amount()

    if table:
        if status == Order.OrderStatus.PAID:
            table.status = Table.TableStatus.AVAILABLE
            table.save()
        elif status == Order.OrderStatus.CANCELLED:
            table.status = Table.TableStatus.AVAILABLE
            table.save()

    if status == Order.OrderStatus.CANCELLED:
        current_items = [{"menu_item": item.menu_item, "quantity": item.quantity} for item in order.items.all()]
        restore_inventory_stock(current_items)

    return order
