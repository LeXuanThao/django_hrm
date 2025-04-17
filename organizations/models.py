from django.db import models
from employees.models import Employee  # Import model Employee

class Organization(models.Model):
    name = models.CharField(max_length=255)  # Tên tổ chức
    address = models.TextField(blank=True)  # Địa chỉ
    phone_number = models.CharField(max_length=15, blank=True)  # Số điện thoại
    email = models.EmailField(blank=True)  # Email liên hệ
    created_at = models.DateTimeField(auto_now_add=True)  # Ngày tạo
    updated_at = models.DateTimeField(auto_now=True)  # Ngày cập nhật

    def __str__(self):
        return self.name


class Department(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)  # Tên phòng ban
    description = models.TextField(blank=True)  # Mô tả phòng ban
    manager = models.OneToOneField(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_department')  # Quản lý phòng ban
    employees = models.ManyToManyField(Employee, blank=True, related_name='departments')  # Nhân sự trực thuộc
    created_at = models.DateTimeField(auto_now_add=True)  # Ngày tạo
    updated_at = models.DateTimeField(auto_now=True)  # Ngày cập nhật

    def __str__(self):
        return f"{self.name} - {self.organization.name}"


class Position(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    name = models.CharField(max_length=255)  # Tên vị trí
    description = models.TextField(blank=True)  # Mô tả vị trí
    created_at = models.DateTimeField(auto_now_add=True)  # Ngày tạo
    updated_at = models.DateTimeField(auto_now=True)  # Ngày cập nhật

    def __str__(self):
        return f"{self.name} - {self.department.name}"


class EmployeeContract(models.Model):
    CONTRACT_TYPE_CHOICES = [
        ('FULL_TIME', 'Full-Time'),
        ('PART_TIME', 'Part-Time'),
        ('INTERNSHIP', 'Internship'),
        ('FREELANCE', 'Freelance'),
        ('PROBATION', 'Probation'),  # Thêm loại hợp đồng Thử việc
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='contracts')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
    start_date = models.DateField()  # Ngày bắt đầu hợp đồng
    end_date = models.DateField(null=True, blank=True)  # Ngày kết thúc hợp đồng (nếu có)
    salary = models.DecimalField(max_digits=10, decimal_places=2)  # Lương
    description = models.TextField(blank=True)  # Mô tả hợp đồng

    def __str__(self):
        return f"{self.employee} - {self.contract_type} ({self.start_date} - {self.end_date or 'Ongoing'})"
