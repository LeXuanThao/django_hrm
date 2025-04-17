from django.contrib import admin
from .models import Organization, Department, Position, EmployeeContract
from employees.models import Employee

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'created_at')
    search_fields = ('name', 'phone_number', 'email')
    ordering = ('name',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'manager', 'created_at')
    search_fields = ('name', 'organization__name', 'manager__account__email')
    ordering = ('organization', 'name')

    fieldsets = (
        ('Thông tin phòng ban', {
            'fields': ('organization', 'name', 'description')
        }),
        ('Quản lý', {
            'fields': ('manager',)
        }),
        ('Nhân sự trực thuộc', {
            'fields': ('employees',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('employees',)  # Hiển thị widget chọn nhiều nhân sự

    # Lọc danh sách nhân viên có thể được chọn làm Manager
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "manager":
            kwargs["queryset"] = Employee.objects.filter(job_title="Manager")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'created_at')
    search_fields = ('name', 'department__name', 'department__organization__name')
    ordering = ('department', 'name')


@admin.register(EmployeeContract)
class EmployeeContractAdmin(admin.ModelAdmin):
    list_display = ('employee', 'contract_type', 'start_date', 'end_date', 'salary')
    search_fields = ('employee__account__email', 'contract_type')
    ordering = ('start_date',)
