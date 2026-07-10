"""Admin configuration for the restaurant application."""

from django.contrib import admin

from .models import Inventory, MenuItem, Order, OrderItem, Reservation, Table


class TableAdmin(admin.ModelAdmin):
    list_display = ("table_number", "capacity", "status")
    list_filter = ("status",)
    search_fields = ("table_number", "status")


class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "available")
    list_filter = ("category", "available")
    search_fields = ("name", "category")


class InventoryAdmin(admin.ModelAdmin):
    list_display = ("menu_item", "quantity", "minimum_stock")
    list_filter = ("minimum_stock",)
    search_fields = ("menu_item__name",)


class ReservationAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "table", "reservation_date", "reservation_time", "status")
    list_filter = ("status", "reservation_date")
    search_fields = ("customer_name", "customer_phone", "table__table_number")


class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "table", "total_amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "table__table_number")
    readonly_fields = ("total_amount", "created_at")


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "menu_item", "quantity", "subtotal")
    list_filter = ("menu_item",)
    search_fields = ("order__id", "menu_item__name")


admin.site.site_header = "Restaurant Management System Administration"
admin.site.site_title = "RMS Admin"
admin.site.index_title = "Restaurant Operations"

admin.site.register(Table, TableAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
