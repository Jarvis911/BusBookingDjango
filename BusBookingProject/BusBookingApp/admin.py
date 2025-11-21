from django.contrib import admin

# Register your models here.
from .models import Bus, Route, Trip, Booking


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('LICENSE_PLATE', 'bus_type', 'total_seats')


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination', 'base_price')


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('route', 'bus', 'departure_time', 'status')
    list_filter = ('status', 'departure_time')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'trip', 'seat_number', 'status')
    list_filter = ('status',)
