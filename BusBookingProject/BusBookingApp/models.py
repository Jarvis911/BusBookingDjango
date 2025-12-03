from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# ... (Model Bus giữ nguyên) ...
class Bus(models.Model):
    LICENSE_PLATE = models.CharField(max_length=20, unique=True)
    bus_type = models.CharField(max_length=50)
    total_seats = models.PositiveIntegerField(default=40)

    def __str__(self):
        return f"{self.LICENSE_PLATE} ({self.total_seats} ghế)"


# 2. Quản lý Tuyến đường
class Route(models.Model):
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    distance_km = models.FloatField(null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=0)
    duration_hours = models.FloatField(help_text="Thời gian di chuyển dự kiến")

    def __str__(self):
        return f"{self.origin} -> {self.destination}"


# ===> MỚI: Model Điểm đón/trả thuộc về Route <===
class RoutePoint(models.Model):
    POINT_TYPE_CHOICES = [
        ('PICKUP', 'Điểm đón'),
        ('DROPOFF', 'Điểm trả'),
        ('BOTH', 'Điểm trung chuyển (Vừa đón vừa trả)'),
    ]

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='points')
    name = models.CharField(max_length=200)  # Tên điểm (Vd: Bến xe Mỹ Đình, Ngã tư Sở)
    address = models.CharField(max_length=500, blank=True)  # Địa chỉ chi tiết
    point_type = models.CharField(max_length=10, choices=POINT_TYPE_CHOICES, default='BOTH')
    order = models.PositiveIntegerField(default=0, help_text="Thứ tự điểm trên hành trình (0, 1, 2...)")
    surcharge = models.DecimalField(max_digits=10, decimal_places=0, default=0,
                                    help_text="Phụ phí nếu đón/trả tại đây (nếu có)")

    class Meta:
        ordering = ['order']  # Sắp xếp theo thứ tự hành trình
        unique_together = ['route', 'order']  # Không thể có 2 điểm cùng thứ tự trên 1 tuyến

    def __str__(self):
        return f"[{self.route.origin}-{self.route.destination}] {self.name} ({self.get_point_type_display()})"


# ... (Model Trip giữ nguyên) ...
class Trip(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='trips')
    bus = models.ForeignKey(Bus, on_delete=models.PROTECT)
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


# 4. Quản lý Đặt vé (CẬP NHẬT LOGIC)
class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Chờ thanh toán'),
        ('CONFIRMED', 'Đã đặt'),
        ('CANCELLED', 'Đã hủy'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='bookings')

    # ===> CẬP NHẬT: Thêm điểm đón/trả <===
    pickup_point = models.ForeignKey(RoutePoint, on_delete=models.PROTECT, related_name='pickup_bookings',
                                     verbose_name="Điểm đón")
    dropoff_point = models.ForeignKey(RoutePoint, on_delete=models.PROTECT, related_name='dropoff_bookings',
                                      verbose_name="Điểm trả")

    seat_number = models.PositiveIntegerField()
    booking_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    price_paid = models.DecimalField(max_digits=10, decimal_places=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['trip', 'seat_number'],
                condition=models.Q(status__in=['PENDING', 'CONFIRMED']),
                name='unique_seat_per_trip'
            )
        ]

    def clean(self):
        # 1. Logic cũ: Kiểm tra ghế
        if self.seat_number > self.trip.bus.total_seats:
            raise ValidationError(f"Ghế số {self.seat_number} không tồn tại.")

        # 2. Logic MỚI: Kiểm tra điểm đón/trả có thuộc Route của Trip không?
        if self.pickup_point.route != self.trip.route:
            raise ValidationError({'pickup_point': "Điểm đón không thuộc lộ trình của chuyến xe này."})

        if self.dropoff_point.route != self.trip.route:
            raise ValidationError({'dropoff_point': "Điểm trả không thuộc lộ trình của chuyến xe này."})

        # 3. Logic MỚI: Kiểm tra loại điểm (Điểm trả thì không được đón, trừ khi là BOTH)
        if self.pickup_point.point_type == 'DROPOFF':
            raise ValidationError({'pickup_point': "Đây là điểm trả khách, không được phép đón."})

        if self.dropoff_point.point_type == 'PICKUP':
            raise ValidationError({'dropoff_point': "Đây là điểm đón khách, không được phép trả."})

        # 4. Logic MỚI: Kiểm tra thứ tự (Điểm đón phải đứng trước điểm trả)
        # Ví dụ: Hà Nội (order=0) -> Ninh Bình (order=1) -> Thanh Hóa (order=2)
        # Đón Ninh Bình thì phải trả ở Thanh Hóa, không được trả ngược về Hà Nội.
        if self.pickup_point.order >= self.dropoff_point.order:
            raise ValidationError("Điểm trả khách phải nằm sau điểm đón khách trong lộ trình.")

    def save(self, *args, **kwargs):
        # Tự động cộng phụ phí (nếu có) vào giá vé
        if not self.price_paid:
            base = self.trip.route.base_price
            surcharge = self.pickup_point.surcharge + self.dropoff_point.surcharge
            self.price_paid = base + surcharge

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Vé {self.id} | Ghế {self.seat_number} | Đón: {self.pickup_point.name} -> Trả: {self.dropoff_point.name}"