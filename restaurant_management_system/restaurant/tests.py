"""
Tests module for the restaurant application.

This file contains automated unit tests to verify the correctness of
models, serializers, views, and helpers within the restaurant application.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class SystemStatusTests(APITestCase):
    """
    Test suite for system status checking.
    """
    def test_api_status_check(self):
        """
        Verify that the status check URL is working, returns 200 OK,
        and provides the expected online system status.
        """
        # Resolve the URL from its name
        url = reverse('api_status_check')
        
        # Perform a GET request to the resolved URL
        response = self.client.get(url)
        
        # Verify the response status code is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the content matches the expected status
        self.assertEqual(response.data['status'], 'online')
        self.assertEqual(response.data['version'], '1.0.0')


from django.test import TestCase
from django.db.models.deletion import ProtectedError
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token
from .models import Table, MenuItem, Inventory, Reservation, Order, OrderItem
import datetime
from decimal import Decimal

class RestaurantModelTests(TestCase):
    """
    Unit tests for the restaurant database models and relations.
    """

    def setUp(self):
        # Create a table for dining
        self.table = Table.objects.create(
            table_number=5,
            capacity=4,
            status=Table.TableStatus.AVAILABLE
        )

        # Create menu items
        self.steak = MenuItem.objects.create(
            name="Ribeye Steak",
            description="Juicy 300g ribeye steak served with fries",
            category=MenuItem.MenuCategory.MAIN_COURSE,
            price=Decimal('29.99'),
            available=True
        )
        self.soda = MenuItem.objects.create(
            name="Cola",
            description="Cold fizzy drink",
            category=MenuItem.MenuCategory.BEVERAGE,
            price=Decimal('2.50'),
            available=True
        )

    def test_table_creation(self):
        """Verify Table details are stored correctly."""
        self.assertEqual(str(self.table), "Table 5 (Capacity: 4)")
        self.assertEqual(self.table.status, Table.TableStatus.AVAILABLE)

    def test_menu_item_creation(self):
        """Verify MenuItem details are stored correctly."""
        self.assertEqual(str(self.steak), "Ribeye Steak (Main Course) - $29.99")

    def test_inventory_creation(self):
        """Verify Inventory tracking and links to MenuItem."""
        inv = Inventory.objects.create(
            menu_item=self.steak,
            quantity=50,
            minimum_stock=10
        )
        self.assertEqual(inv.quantity, 50)
        self.assertEqual(inv.minimum_stock, 10)
        self.assertEqual(inv.menu_item, self.steak)

    def test_reservation_creation(self):
        """Verify Reservation details and relationship with Table."""
        res_date = datetime.date(2026, 7, 10)
        res_time = datetime.time(19, 0)
        res = Reservation.objects.create(
            customer_name="Alice Smith",
            customer_phone="123-456-7890",
            table=self.table,
            reservation_date=res_date,
            reservation_time=res_time,
            number_of_people=4,
            status=Reservation.ReservationStatus.CONFIRMED
        )
        self.assertEqual(res.customer_name, "Alice Smith")
        self.assertEqual(res.table, self.table)

    def test_order_and_order_item_calculations(self):
        """
        Verify that creating OrderItems correctly updates:
        - OrderItem subtotal (quantity * MenuItem price)
        - Parent Order's total_amount
        """
        order = Order.objects.create(
            table=self.table,
            status=Order.OrderStatus.PENDING
        )
        self.assertEqual(order.total_amount, Decimal('0.00'))

        # Add 2x Steaks
        item1 = OrderItem.objects.create(
            order=order,
            menu_item=self.steak,
            quantity=2
        )
        # 2 * 29.99 = 59.98
        self.assertEqual(item1.subtotal, Decimal('59.98'))
        
        # Refresh order from db
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal('59.98'))

        # Add 3x Soda
        item2 = OrderItem.objects.create(
            order=order,
            menu_item=self.soda,
            quantity=3
        )
        # 3 * 2.50 = 7.50
        self.assertEqual(item2.subtotal, Decimal('7.50'))

        # Refresh order from db
        order.refresh_from_db()
        # 59.98 + 7.50 = 67.48
        self.assertEqual(order.total_amount, Decimal('67.48'))

    def test_menu_item_deletion_protection(self):
        """
        Verify that a MenuItem cannot be deleted if it is linked
        to a historical OrderItem (on_delete=models.PROTECT).
        """
        order = Order.objects.create(table=self.table)
        OrderItem.objects.create(
            order=order,
            menu_item=self.steak,
            quantity=1
        )
        
        # Deleting steak should raise ProtectedError
        with self.assertRaises(ProtectedError):
            self.steak.delete()


class AuthenticationAndReportTests(APITestCase):
    """Tests for authentication helpers and management reports."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="manager",
            password="securepassword123"
        )
        self.table = Table.objects.create(
            table_number=9,
            capacity=4,
            status=Table.TableStatus.AVAILABLE
        )
        self.reserved_table = Table.objects.create(
            table_number=10,
            capacity=2,
            status=Table.TableStatus.RESERVED
        )
        self.menu_item = MenuItem.objects.create(
            name="Soup",
            description="Warm soup",
            category=MenuItem.MenuCategory.APPETIZER,
            price=Decimal('6.00'),
            available=True
        )
        self.inventory = Inventory.objects.create(
            menu_item=self.menu_item,
            quantity=2,
            minimum_stock=5
        )
        Order.objects.create(
            table=self.table,
            total_amount=Decimal('18.00'),
            status=Order.OrderStatus.PAID,
            created_at=timezone.now()
        )

    def test_login_returns_token(self):
        """Authenticate a user and receive a token for API access."""
        url = reverse('login')
        response = self.client.post(url, {
            'username': 'manager',
            'password': 'securepassword123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'manager')

    def test_daily_sales_report_returns_summary(self):
        """Daily sales report should summarize paid orders for the selected day."""
        url = reverse('daily-sales-report')
        response = self.client.get(url, {'date': timezone.localdate().isoformat()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_count'], 1)
        self.assertEqual(Decimal(response.data['total_sales']), Decimal('18.00'))

    def test_token_endpoint_and_logout(self):
        """Token issuance and logout should work for authenticated users."""
        token_url = reverse('obtain-auth-token')
        token_response = self.client.post(token_url, {
            'username': 'manager',
            'password': 'securepassword123'
        }, format='json')
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        self.assertIn('token', token_response.data)

        token = Token.objects.get(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        logout_response = self.client.post(reverse('logout'))
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertFalse(Token.objects.filter(key=token.key).exists())

    def test_low_stock_report_lists_items_below_threshold(self):
        """Low-stock report should include inventory that is at or below minimum stock."""
        url = reverse('low-stock-report')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['menu_item']['name'], 'Soup')

    def test_available_and_reserved_table_reports(self):
        """Table reports should distinguish between available and reserved tables."""
        available_url = reverse('available-tables-report')
        reserved_url = reverse('reserved-tables-report')

        available_response = self.client.get(available_url)
        reserved_response = self.client.get(reserved_url)

        self.assertEqual(available_response.status_code, status.HTTP_200_OK)
        self.assertEqual(reserved_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(available_response.data), 1)
        self.assertEqual(len(reserved_response.data), 1)


class RestaurantAPITests(APITestCase):
    """
    Test suite for the REST API endpoints and CRUD workflows.
    """

    def setUp(self):
        # Create a test user for DRF authentication validation checks
        self.user = User.objects.create_user(
            username="teststaff",
            password="securepassword123"
        )
        # Authenticate the API test client so write operations (POST, PUT, DELETE) are permitted
        self.client.force_authenticate(user=self.user)

        # Setup base objects for API tests
        self.table = Table.objects.create(
            table_number=1,
            capacity=2,
            status=Table.TableStatus.AVAILABLE
        )
        self.menu_item = MenuItem.objects.create(
            name="Garlic Bread",
            description="Crispy toast with garlic butter",
            category=MenuItem.MenuCategory.APPETIZER,
            price=Decimal('5.50'),
            available=True
        )
        self.inventory = Inventory.objects.create(
            menu_item=self.menu_item,
            quantity=50,
            minimum_stock=5
        )

    def test_create_table(self):
        """Test POST request to create a Table."""
        url = reverse('table-list')
        data = {
            "table_number": 2,
            "capacity": 6,
            "status": "Available"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Table.objects.count(), 2)
        self.assertEqual(response.data['capacity'], 6)

    def test_list_tables(self):
        """Test GET request to list Tables."""
        url = reverse('table-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Results should be paginated (see PAGE_SIZE = 10 in settings)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_menu_item(self):
        """Test POST request to create a MenuItem."""
        url = reverse('menuitem-list')
        data = {
            "name": "Chicken Parmesan",
            "description": "Crispy chicken breast with marinara sauce and cheese",
            "category": "Main Course",
            "price": "18.99",
            "available": True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Chicken Parmesan")

    def test_create_inventory_record(self):
        """Test POST request to create an Inventory record."""
        url = reverse('inventory-list')
        data = {
            "menu_item": self.menu_item.id,
            "quantity": 100,
            "minimum_stock": 15
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quantity'], 100)

    def test_create_reservation_success(self):
        """Test booking a reservation that satisfies all validation checks."""
        url = reverse('reservation-list')
        data = {
            "customer_name": "Bob Dylan",
            "customer_phone": "555-0199",
            "table": self.table.id,
            "reservation_date": str(timezone.localdate() + datetime.timedelta(days=1)),
            "reservation_time": "18:30:00",
            "number_of_people": 2,
            "status": "Pending"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_reservation_fails_exceeds_capacity(self):
        """Test booking a reservation where group size exceeds the table seating capacity."""
        url = reverse('reservation-list')
        data = {
            "customer_name": "Too Many Diners",
            "customer_phone": "555-9999",
            "table": self.table.id,
            # Seating capacity of self.table is 2, trying to reserve for 4
            "reservation_date": str(timezone.localdate() + datetime.timedelta(days=1)),
            "reservation_time": "19:00:00",
            "number_of_people": 4,
            "status": "Pending"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("number_of_people", response.data)

    def test_create_order_nested_items_success(self):
        """Test creating an Order with nested OrderItems via a single POST request."""
        url = reverse('order-list')
        data = {
            "table": self.table.id,
            "status": "Pending",
            "items": [
                {
                    "menu_item": self.menu_item.id,
                    "quantity": 3
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Expected calculation: 3 * 5.50 = 16.50
        self.assertEqual(Decimal(response.data['total_amount']), Decimal('16.50'))
        self.assertEqual(len(response.data['items']), 1)
        self.assertEqual(response.data['items'][0]['subtotal'], '16.50')

    def test_reservation_double_booking_prevention(self):
        """Test booking a reservation that overlaps with an existing reservation within 2 hours."""
        # Create an existing reservation
        res_date = timezone.localdate() + datetime.timedelta(days=2)
        res_time = datetime.time(12, 0)
        Reservation.objects.create(
            customer_name="John Doe",
            customer_phone="555-1111",
            table=self.table,
            reservation_date=res_date,
            reservation_time=res_time,
            number_of_people=2,
            status="Confirmed"
        )
        
        # Try to reserve the same table at 13:00 (overlaps since interval is 2 hours)
        url = reverse('reservation-list')
        data = {
            "customer_name": "Jane Doe",
            "customer_phone": "555-2222",
            "table": self.table.id,
            "reservation_date": str(res_date),
            "reservation_time": "13:00:00",
            "number_of_people": 2,
            "status": "Pending"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Assert custom error message is in the response details
        self.assertIn("already booked", str(response.data))

    def test_reservation_automated_table_status_today(self):
        """Test that confirming a booking for today updates the table status to Reserved."""
        future_time = (timezone.localtime() + datetime.timedelta(hours=1)).time().strftime('%H:%M:%S')
        url = reverse('reservation-list')
        data = {
            "customer_name": "Today Diner",
            "customer_phone": "555-3333",
            "table": self.table.id,
            "reservation_date": str(timezone.localdate()),
            "reservation_time": future_time,
            "number_of_people": 2,
            "status": "Confirmed"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verify table status changed to Reserved
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, Table.TableStatus.RESERVED)

    def test_order_deducts_inventory(self):
        """Test that placing an order automatically reduces stock levels in Inventory."""
        # Initial stock count
        self.assertEqual(self.inventory.quantity, 50)
        
        url = reverse('order-list')
        data = {
            "table": self.table.id,
            "status": "Pending",
            "items": [
                {
                    "menu_item": self.menu_item.id,
                    "quantity": 5
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify stock has been reduced by 5
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 45)

    def test_order_fails_if_insufficient_inventory(self):
        """Test that placing an order fails if the requested quantity exceeds stock."""
        url = reverse('order-list')
        data = {
            "table": self.table.id,
            "status": "Pending",
            "items": [
                {
                    "menu_item": self.menu_item.id,
                    "quantity": 60 # Only 50 in stock
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Assert clean user-friendly validation message
        self.assertIn("Insufficient inventory", str(response.data))

    def test_cancelling_order_restores_inventory(self):
        """Test that cancelling an order restores stock levels."""
        # Create order (stock becomes 45)
        url = reverse('order-list')
        data = {
            "table": self.table.id,
            "status": "Pending",
            "items": [
                {
                    "menu_item": self.menu_item.id,
                    "quantity": 5
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        order_id = response.data['id']
        
        # Verify stock is 45
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 45)
        
        # Cancel order via PUT/PATCH update
        url_detail = reverse('order-detail', kwargs={'pk': order_id})
        update_data = {
            "status": "Cancelled"
        }
        response = self.client.patch(url_detail, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify stock was restored to 50
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 50)



