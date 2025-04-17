from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class AccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class Account(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = AccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Employee(models.Model):
    JOB_TITLE_CHOICES = [
        ('STAFF', 'Staff'),
        ('STAFF_MANAGER', 'Staff Manager'),
        ('MANAGER', 'Manager'),
    ]

    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='employee_profile')
    date_of_birth = models.DateField(null=True, blank=True)  # Ngày sinh
    hire_date = models.DateField(null=True, blank=True)  # Ngày vào làm
    phone_number = models.CharField(max_length=15, blank=True)  # Số điện thoại
    address = models.TextField(blank=True)  # Địa chỉ
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        blank=True
    )  # Giới tính
    job_title = models.CharField(
        max_length=20,
        choices=JOB_TITLE_CHOICES,
        default='STAFF'
    )  # Chức danh công việc

    def __str__(self):
        return f"{self.account.first_name} {self.account.last_name} - {self.job_title}"

class EmployeeDocument(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document_name = models.CharField(max_length=255)  # Tên tài liệu
    document_file = models.FileField(upload_to='storage/employee_documents/')  # Thay đổi đường dẫn upload
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Thời gian tải lên

    def __str__(self):
        return f"{self.document_name} ({self.employee})"
