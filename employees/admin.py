from django.contrib import admin
from .models import Account, Employee, EmployeeDocument

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        ('Account Information', {
            'fields': ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
        }),
        ('Password', {
            'fields': ('password',)
        }),
    )

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('account', 'job_title', 'hire_date', 'phone_number', 'address', 'gender')
    search_fields = ('account__email', 'job_title', 'phone_number', 'address')
    ordering = ('account__email',)

    fieldsets = (
        ('Thông tin tài khoản', {
            'fields': ('account',)
        }),
        ('Thông tin cá nhân', {
            'fields': ('date_of_birth', 'gender', 'phone_number', 'address')
        }),
        ('Thông tin công việc', {
            'fields': ('job_title', 'hire_date')
        }),
    )

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'document_name', 'uploaded_at')
    search_fields = ('employee__account__email', 'document_name')
    ordering = ('uploaded_at',)

