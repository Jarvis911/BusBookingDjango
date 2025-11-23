from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Trip, Booking, User
from .serializers import TripSerializer, BookingSerializer, UserRegistrationSerializer
from datetime import datetime
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    # Client ID mà bạn lấy từ Google Cloud Console
    client_class = OAuth2Client
    # Callback URL phải khớp với cái khai báo trên Google Console
    # Vì dùng API, thường ta set url của frontend hoặc để trống tùy setup
    callback_url = "http://localhost:3000"


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny] # Cho phép khách vãng lai truy cập

# 1. API Tìm kiếm chuyến xe
# GET /api/trips/?origin=Hanoi&destination=Sapa&date=2023-12-25
class TripListView(generics.ListAPIView):
    serializer_class = TripSerializer
    permission_classes = [permissions.AllowAny]  # Ai cũng xem được

    def get_queryset(self):
        queryset = Trip.objects.filter(status='SCHEDULED')

        # Lọc theo params trên URL
        origin = self.request.query_params.get('origin')
        destination = self.request.query_params.get('destination')
        date_str = self.request.query_params.get('date')

        if origin:
            queryset = queryset.filter(route__origin__icontains=origin)
        if destination:
            queryset = queryset.filter(route__destination__icontains=destination)
        if date_str:
            # Giả sử format yyyy-mm-dd
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(departure_time__date=date_obj)
            except ValueError:
                pass

        return queryset


# 2. API Xem chi tiết 1 chuyến (để lấy lại sơ đồ ghế mới nhất)
# GET /api/trips/1/
class TripDetailView(generics.RetrieveAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer


# 3. API Đặt vé
# POST /api/bookings/
class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]  # Phải đăng nhập mới được đặt

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Lưu booking (logic nằm trong serializer.create)
        self.perform_create(serializer)

        return Response(
            {"message": "Đặt chỗ thành công! Vui lòng thanh toán.", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )