from rest_framework import generics, permissions, status
from rest_framework.response import Response
from datetime import datetime

# Import models & serializers
from .models import Trip, Booking
from .serializers import TripSerializer, BookingSerializer
# (Xóa UserRegistrationSerializer khỏi import)

# Import cho Google Login
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

# Import cho Swagger doc
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes


# --------------------------------------
# 1. AUTH VIEWS
# --------------------------------------

# Chỉ giữ lại mỗi cái này vì library yêu cầu phải config Adapter
class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "http://localhost:3000"


# --------------------------------------
# 2. BUSINESS VIEWS
# --------------------------------------
# (Giữ nguyên toàn bộ logic TripListView, TripDetailView, BookingCreateView cũ)
# ... Copy lại phần logic Business cũ của bạn vào đây ...
class TripListView(generics.ListAPIView):
    serializer_class = TripSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Trip.objects.filter(status='SCHEDULED') \
            .select_related('route', 'bus') \
            .prefetch_related('route__points')

        origin = self.request.query_params.get('origin')
        destination = self.request.query_params.get('destination')
        date_str = self.request.query_params.get('date')

        if origin:
            queryset = queryset.filter(route__origin__icontains=origin)
        if destination:
            queryset = queryset.filter(route__destination__icontains=destination)
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(departure_time__date=date_obj)
            except ValueError:
                pass

        return queryset


class TripDetailView(generics.RetrieveAPIView):
    serializer_class = TripSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Trip.objects.all().select_related('route', 'bus').prefetch_related('route__points')


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Đặt vé thành công!", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )