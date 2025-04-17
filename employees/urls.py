from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import EmployeeViewSet, EmployeeDocumentViewSet

# Sử dụng router để tự động tạo các endpoint
router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'employee-documents', EmployeeDocumentViewSet, basename='employee-document')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),  # Tự động thêm các endpoint từ router
]