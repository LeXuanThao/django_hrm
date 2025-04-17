from django.contrib import admin
from .models import Account, Employee

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
    list_display = ('account', 'hire_date', 'phone_number', 'address', 'gender')
    search_fields = ('account__email', 'phone_number', 'address')
    ordering = ('account__email',)

    # Chia các trường thành các fieldset
    fieldsets = (
        ('Account Information', {
            'fields': ('account',)
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'gender', 'phone_number', 'address')
        }),
        ('Working Information', {
            'fields': ('hire_date',)
        }),
    )

