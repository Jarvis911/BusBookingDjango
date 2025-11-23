from django.urls import path, include
from .views import TripListView, TripDetailView, BookingCreateView, GoogleLogin, UserRegistrationView

urlpatterns = [
    path('trips/', TripListView.as_view(), name='trip-list'),
    path('trips/<int:pk>/', TripDetailView.as_view(), name='trip-detail'),
    path('bookings/', BookingCreateView.as_view(), name='booking-create'),
    # API đăng nhập thường (username/pass)
    path('auth/', include('dj_rest_auth.urls')),
    # API đăng ký thường
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    # API đăng nhập Google
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('register/', UserRegistrationView.as_view(), name='register'),
]