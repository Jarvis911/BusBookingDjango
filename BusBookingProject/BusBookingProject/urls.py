# project_name/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token
# Import các view của Swagger (nếu bạn đã cài drf-spectacular ở bước trước)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # 1. Trang quản trị Django (Admin)
    path('admin/', admin.site.urls),
    path('api/v1/', include('BusBookingApp.urls')),
    # 3. Cấu hình Swagger API Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# 4. Cấu hình phục vụ file Media (Ảnh xe, avatar...) trong môi trường DEV
# (Django không tự phục vụ file media khi DEBUG=True trừ khi cấu hình dòng này)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)