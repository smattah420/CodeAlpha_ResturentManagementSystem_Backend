"""Models for the restaurant management system."""

from django.db import models


class Table(models.Model):
    """Represent a physical table in the restaurant."""

    class TableStatus(models.TextChoices):
        AVAILABLE = "Available", "Available"
        RESERVED = "Reserved", "Reserved"
        OCCUPIED = "Occupied", "Occupied"

    table_number = models.PositiveIntegerField(
        unique=True,
        verbose_name="Table Number",
        help_text="Unique identifier for the physical table",
    )
    capacity = models.PositiveIntegerField(
        verbose_name="Seating Capacity",
        help_text="Maximum number of people that can sit at this table",
    )
    status = models.CharField(
        max_length=20,
        choices=TableStatus.choices,
        default=TableStatus.AVAILABLE,
        verbose_name="Current Status",
        help_text="The current occupancy state of the table",
    )

    class Meta:
        verbose_name = "Dining Table"
        verbose_name_plural = "Dining Tables"
        ordering = ["table_number"]

    def __str__(self):
        return f"Table {self.table_number} (Capacity: {self.capacity})"


class MenuItem(models.Model):
    """Represent an item available on the restaurant menu."""

    class MenuCategory(models.TextChoices):
        APPETIZER = "Appetizer", "Appetizer"
        MAIN_COURSE = "Main Course", "Main Course"
        DESSERT = "Dessert", "Dessert"
        BEVERAGE = "Beverage", "Beverage"

    name = models.CharField(max_length=150, unique=True, verbose_name="Item Name")
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Details about ingredients, portion size, and allergy info",
    )
    category = models.CharField(
        max_length=50,
        choices=MenuCategory.choices,
        verbose_name="Category",
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Price ($)")
    available = models.BooleanField(
        default=True,
        verbose_name="Is Available",
        help_text="Designates whether this item can currently be ordered",
    )

    class Meta:
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.category}) - ${self.price}"


class Inventory(models.Model):
    """Track inventory quantities for specific menu items."""

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="inventory_records",
        verbose_name="Menu Item",
    )
    quantity = models.PositiveIntegerField(default=0, verbose_name="Current Quantity in Stock")
    minimum_stock = models.PositiveIntegerField(
        default=5,
        verbose_name="Minimum Safety Stock Level",
        help_text="Alert threshold. When quantity falls below this, reordering is required.",
    )

    class Meta:
        verbose_name = "Inventory Record"
        verbose_name_plural = "Inventory Records"

    def __str__(self):
        return f"Inventory for {self.menu_item.name}: {self.quantity} in stock (Min: {self.minimum_stock})"


class Reservation(models.Model):
    """Track table bookings made by customers."""

    class ReservationStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        CONFIRMED = "Confirmed", "Confirmed"
        CANCELLED = "Cancelled", "Cancelled"

    customer_name = models.CharField(max_length=100, verbose_name="Customer Name")
    customer_phone = models.CharField(max_length=20, verbose_name="Customer Phone Number")
    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="Assigned Table",
    )
    reservation_date = models.DateField(verbose_name="Reservation Date")
    reservation_time = models.TimeField(verbose_name="Reservation Time")
    number_of_people = models.PositiveIntegerField(verbose_name="Number of People")
    status = models.CharField(
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
        verbose_name="Reservation Status",
    )

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ["reservation_date", "reservation_time"]

    def __str__(self):
        return f"Reservation for {self.customer_name} on {self.reservation_date} at {self.reservation_time} (Table {self.table.table_number})"


class Order(models.Model):
    """Represent a customer order transaction."""

    class OrderStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        PREPARING = "Preparing", "Preparing"
        SERVED = "Served", "Served"
        PAID = "Paid", "Paid"
        CANCELLED = "Cancelled", "Cancelled"

    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Table",
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Amount ($)",
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        verbose_name="Order Status",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ordered At")

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        table_str = f"Table {self.table.table_number}" if self.table else "Takeaway/Delivery"
        return f"Order #{self.pk} - {table_str} ({self.status}) - ${self.total_amount}"

    def update_total_amount(self):
        """Calculate and update the total order amount from its items."""
        self.total_amount = sum(item.subtotal for item in self.items.all())
        self.save()


class OrderItem(models.Model):
    """Represent an individual line item in a customer order."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Parent Order",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Menu Item",
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity Ordered")
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        verbose_name="Subtotal ($)",
    )

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} for Order #{self.order.pk}"

    def save(self, *args, **kwargs):
        """Calculate the subtotal and refresh the parent order total."""
        self.subtotal = self.quantity * self.menu_item.price
        super().save(*args, **kwargs)
        self.order.update_total_amount()
