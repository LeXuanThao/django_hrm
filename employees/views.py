from rest_framework import viewsets
from .models import Employee
from .serializers import EmployeeSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint cho phép quản lý danh sách nhân viên.
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
