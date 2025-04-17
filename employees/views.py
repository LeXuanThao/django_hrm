from rest_framework import viewsets
from .models import Employee, EmployeeDocument
from .serializers import EmployeeSerializer, EmployeeDocumentSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint cho phép quản lý danh sách nhân viên.
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint cho phép quản lý tài liệu nhân sự.
    """
    queryset = EmployeeDocument.objects.all()
    serializer_class = EmployeeDocumentSerializer
