from django.urls import path, include
from .views import (
    TripListView,
    TripDetailView,
    BookingCreateView,
    GoogleLogin
)

urlpatterns = [
    # --- BUS & BOOKING API (Giữ nguyên logic nghiệp vụ) ---
    path('trips/', TripListView.as_view(), name='trip-list'),
    path('trips/<int:pk>/', TripDetailView.as_view(), name='trip-detail'),
    path('bookings/', BookingCreateView.as_view(), name='booking-create'),

    # --- AUTH API (Dùng thư viện) ---
    # 1. Login, Logout, User Info, Password Reset...
    # Endpoint: /api/auth/login/, /api/auth/logout/, /api/auth/user/...
    path('auth/', include('dj_rest_auth.urls')),

    # 2. Registration (Đăng ký tài khoản thường)
    # Endpoint: /api/auth/registration/
    path('auth/registration/', include('dj_rest_auth.registration.urls')),

    # 3. Google Login (Vẫn cần khai báo view này để map với Google Adapter)
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
]