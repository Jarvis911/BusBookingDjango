from rest_framework import serializers
from .models import Bus, Route, Trip, Booking, User
from django.db import IntegrityError
from rest_framework.validators import UniqueValidator


# Serializer hiển thị thông tin Tuyến đường
class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'origin', 'destination', 'base_price', 'duration_hours']


# Serializer hiển thị thông tin Chuyến đi (Kèm sơ đồ ghế)
class TripSerializer(serializers.ModelSerializer):
    route = RouteSerializer(read_only=True)
    bus_name = serializers.CharField(source='bus.LICENSE_PLATE', read_only=True)
    seat_map = serializers.SerializerMethodField()  # Trường tự tính toán

    class Meta:
        model = Trip
        fields = ['id', 'route', 'bus_name', 'departure_time', 'seat_map']

    def get_seat_map(self, obj):
        """
        Trả về danh sách trạng thái của tất cả các ghế trên xe.
        Frontend sẽ dùng cái này để vẽ màu (Xanh: Trống, Đỏ: Đã đặt).
        """
        total_seats = obj.bus.total_seats
        # Lấy danh sách các ghế đã được đặt (PENDING hoặc CONFIRMED)
        booked_seats = obj.bookings.filter(
            status__in=['PENDING', 'CONFIRMED']
        ).values_list('seat_number', flat=True)

        seats = []
        for i in range(1, total_seats + 1):
            seats.append({
                'seat_number': i,
                'is_available': i not in booked_seats
            })
        return seats


# Serializer để Đặt vé (Validate dữ liệu đầu vào)
class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['trip', 'seat_number']

    def create(self, validated_data):
        # Lấy user từ context (người đang đăng nhập)
        user = self.context['request'].user

        try:
            # Tạo booking
            booking = Booking.objects.create(
                user=user,
                status='PENDING',  # Mặc định là chờ thanh toán
                price_paid=validated_data['trip'].route.base_price,  # Lấy giá hiện tại
                **validated_data
            )
            return booking

        except IntegrityError:
            # Bắt lỗi nếu Database báo trùng (Unique Constraint)
            raise serializers.ValidationError(
                {"seat_number": "Ghế này vừa bị người khác đặt mất rồi!"}
            )


class UserRegistrationSerializer(serializers.ModelSerializer):
    # Email là bắt buộc và phải duy nhất
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Email này đã được sử dụng.")]
    )
    # Username cũng phải duy nhất
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all(), message="Tên đăng nhập này đã tồn tại.")]
    )
    # Password: chỉ viết (write_only), không bao giờ trả về trong response
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    # Các thông tin phụ (tùy chọn)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        # QUAN TRỌNG: Sử dụng create_user để mật khẩu được mã hóa (hash)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user