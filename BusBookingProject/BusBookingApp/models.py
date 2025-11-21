from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# 1. Quản lý Xe
class Bus(models.Model):
    LICENSE_PLATE = models.CharField(max_length=20, unique=True)  # Biển số
    bus_type = models.CharField(max_length=50)  # Vd: Giường nằm, Limousine
    total_seats = models.PositiveIntegerField(default=40)  # Tổng số ghế (để validate)

    def __str__(self):
        return f"{self.LICENSE_PLATE} ({self.total_seats} ghế)"


# 2. Quản lý Tuyến đường (Địa điểm & Giá)
class Route(models.Model):
    origin = models.CharField(max_length=100)  # Điểm đi
    destination = models.CharField(max_length=100)  # Điểm đến
    distance_km = models.FloatField(null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=0)  # Giá vé chuẩn
    duration_hours = models.FloatField(help_text="Thời gian di chuyển dự kiến")

    def __str__(self):
        return f"{self.origin} -> {self.destination}"


# 3. Quản lý Chuyến đi (Cụ thể hóa thời gian)
class Trip(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='trips')
    bus = models.ForeignKey(Bus, on_delete=models.PROTECT)  # Không cho xóa xe nếu đã có chuyến
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[('SCHEDULED', 'Sắp chạy'), ('RUNNING', 'Đang chạy'), ('COMPLETED', 'Hoàn thành'),
                 ('CANCELLED', 'Hủy')],
        default='SCHEDULED'
    )

    def __str__(self):
        return f"{self.route} | {self.departure_time.strftime('%d/%m %H:%M')}"

    @property
    def available_seats(self):
        # Lấy danh sách ghế đã đặt
        booked_seats = self.bookings.filter(status='CONFIRMED').values_list('seat_number', flat=True)
        # Trả về danh sách ghế còn trống (giả sử ghế đánh số từ 1 đến total_seats)
        all_seats = range(1, self.bus.total_seats + 1)
        return [seat for seat in all_seats if seat not in booked_seats]


# 4. Quản lý Đặt vé (Quan trọng nhất)
class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Chờ thanh toán'),
        ('CONFIRMED', 'Đã đặt'),
        ('CANCELLED', 'Đã hủy'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='bookings')
    seat_number = models.PositiveIntegerField()  # Số ghế (Vd: 1, 2, 3...)
    booking_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    price_paid = models.DecimalField(max_digits=10,
                                     decimal_places=0)  # Lưu giá tại thời điểm đặt (phòng khi giá Route thay đổi)

    class Meta:
        # Ràng buộc duy nhất: Một chuyến đi không thể có 2 vé cùng số ghế (trừ khi vé kia đã hủy)
        constraints = [
            models.UniqueConstraint(
                fields=['trip', 'seat_number'],
                condition=models.Q(status__in=['PENDING', 'CONFIRMED']),
                name='unique_seat_per_trip'
            )
        ]

    def clean(self):
        # Kiểm tra logic: Ghế đặt không được lớn hơn số ghế của xe
        if self.seat_number > self.trip.bus.total_seats:
            raise ValidationError(
                f"Ghế số {self.seat_number} không tồn tại (Xe chỉ có {self.trip.bus.total_seats} ghế).")

    def save(self, *args, **kwargs):
        self.full_clean()  # Gọi hàm clean trước khi lưu
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Vé {self.id} | {self.trip} | Ghế {self.seat_number}"