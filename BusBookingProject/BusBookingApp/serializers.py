from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Bus, Route, Trip, Booking, RoutePoint


# Chỉ giữ lại các Serializer nghiệp vụ (RoutePoint, Route, Trip, Booking)
# ... Copy lại 4 class serializer logic cũ của bạn vào đây ...

class RoutePointSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_point_type_display', read_only=True)

    class Meta:
        model = RoutePoint
        fields = ['id', 'name', 'address', 'point_type', 'type_display', 'order', 'surcharge']


class RouteSerializer(serializers.ModelSerializer):
    points = RoutePointSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = ['id', 'origin', 'destination', 'base_price', 'duration_hours', 'points']


class TripSerializer(serializers.ModelSerializer):
    route = RouteSerializer(read_only=True)
    bus_name = serializers.CharField(source='bus.LICENSE_PLATE', read_only=True)
    seat_map = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = ['id', 'route', 'bus_name', 'departure_time', 'seat_map']

    def get_seat_map(self, obj):
        total_seats = obj.bus.total_seats
        booked_seats = obj.bookings.filter(status__in=['PENDING', 'CONFIRMED']).values_list('seat_number', flat=True)
        seats = []
        for i in range(1, total_seats + 1):
            seats.append({'seat_number': i, 'is_available': i not in booked_seats})
        return seats


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'trip', 'seat_number', 'pickup_point', 'dropoff_point', 'price_paid', 'status', 'booking_time']
        read_only_fields = ['price_paid', 'status', 'booking_time']

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request else None
        instance = Booking(
            user=user,
            trip=data.get('trip'),
            seat_number=data.get('seat_number'),
            pickup_point=data.get('pickup_point'),
            dropoff_point=data.get('dropoff_point')
        )
        try:
            instance.clean()
        except DjangoValidationError as e:
            if hasattr(e, 'message_dict'):
                raise serializers.ValidationError(e.message_dict)
            else:
                raise serializers.ValidationError(str(e))
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        booking = Booking.objects.create(user=user, **validated_data)
        return booking