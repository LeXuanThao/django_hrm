from django.contrib import admin
from django.utils.html import format_html
from .models import (
    WorkType, WorkMode, EmployeeWorkMode, LeaveType, LeaveRequest, LeaveBalance,
    WorkSchedule, WorkModeOverrideDate, AttendanceRecord, DailyAttendanceSummary
)

@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ('employee', 'work_type', 'description')
    search_fields = ('employee__account__email', 'work_type')
    ordering = ('work_type',)


class WorkScheduleInline(admin.TabularInline):
    model = WorkSchedule
    extra = 1
    fields = ('day_of_week', 'is_working_day', 'start_time', 'end_time', 'break_start_time', 'break_end_time', 'working_hours')
    readonly_fields = ('working_hours',)


class WorkModeOverrideDateInline(admin.TabularInline):
    model = WorkModeOverrideDate
    extra = 0
    fields = ('date', 'is_working_day', 'description', 'start_time', 'end_time')


@admin.register(WorkMode)
class WorkModeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'working_hours_per_day', 'working_days_per_week', 'flexible_hours', 'is_active')
    list_filter = ('is_active', 'flexible_hours', 'requires_check_in')
    search_fields = ('name', 'code', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Working Time Configuration', {
            'fields': ('working_hours_per_day', 'working_days_per_week', 'flexible_hours', 
                       'requires_check_in', 'break_duration_minutes')
        }),
    )
    inlines = [WorkScheduleInline, WorkModeOverrideDateInline]


@admin.register(EmployeeWorkMode)
class EmployeeWorkModeAdmin(admin.ModelAdmin):
    list_display = ('employee', 'work_mode', 'start_date', 'end_date', 'is_active')
    list_filter = ('work_mode', 'start_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'work_mode__name')
    autocomplete_fields = ('employee', 'work_mode')
    date_hierarchy = 'start_date'


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'paid', 'max_days_per_year', 'is_active')
    list_filter = ('is_active', 'paid', 'require_approval')
    search_fields = ('name', 'code', 'description')


class LeaveBalanceInline(admin.TabularInline):
    model = LeaveBalance
    extra = 0
    fields = ('leave_type', 'year', 'total_days', 'used_days')
    readonly_fields = ('used_days',)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'days_count', 'status')
    list_filter = ('status', 'leave_type', 'start_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')
    autocomplete_fields = ('employee', 'leave_type', 'approved_by')
    date_hierarchy = 'start_date'
    readonly_fields = ('days_count',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # If not superuser, only show leave requests for employee and subordinates
        if not request.user.is_superuser:
            return qs.filter(employee__manager=request.user.employee)
        return qs


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'total_days', 'used_days', 'remaining_days')
    list_filter = ('year', 'leave_type')
    search_fields = ('employee__first_name', 'employee__last_name')
    autocomplete_fields = ('employee', 'leave_type')
    readonly_fields = ('used_days', 'remaining_days')


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('work_mode', 'day_of_week', 'is_working_day', 'start_time', 'end_time', 'working_hours')
    list_filter = ('is_working_day', 'work_mode', 'day_of_week')
    readonly_fields = ('working_hours',)


@admin.register(WorkModeOverrideDate)
class WorkModeOverrideDateAdmin(admin.ModelAdmin):
    list_display = ('date', 'work_mode', 'is_working_day', 'description')
    list_filter = ('is_working_day', 'work_mode', 'date')
    date_hierarchy = 'date'
    search_fields = ('description', 'work_mode__name')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'record_date', 'record_time', 'record_type', 'status', 'is_manual')
    list_filter = ('record_type', 'status', 'record_date', 'is_manual')
    search_fields = ('employee__first_name', 'employee__last_name', 'note')
    date_hierarchy = 'record_date'
    autocomplete_fields = ('employee', 'created_by')
    readonly_fields = ('ip_address', 'device_info')
    fieldsets = (
        (None, {
            'fields': ('employee', 'record_date', 'record_time', 'record_type', 'status')
        }),
        ('Additional Information', {
            'fields': ('location', 'note', 'is_manual', 'created_by')
        }),
        ('System Information', {
            'fields': ('ip_address', 'device_info'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if obj.is_manual and not obj.created_by:
            try:
                obj.created_by = request.user.employee
            except:
                pass
        super().save_model(request, obj, form, change)


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    fk_name = 'summary'  # Chỉ định khóa ngoại đúng
    extra = 0
    fields = ('record_time', 'record_type', 'status')
    readonly_fields = ('record_time', 'record_type', 'status')
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyAttendanceSummary)
class DailyAttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'formatted_first_check_in', 'formatted_last_check_out', 
                    'status_colored', 'total_hours', 'is_complete')
    list_filter = ('status', 'date', 'is_complete')
    search_fields = ('employee__first_name', 'employee__last_name', 'note')
    date_hierarchy = 'date'
    autocomplete_fields = ('employee',)
    readonly_fields = ('total_hours', 'is_complete')
    inlines = [AttendanceRecordInline]
    
    def formatted_first_check_in(self, obj):
        if obj.first_check_in:
            return obj.first_check_in.strftime('%H:%M:%S')
        return '-'
    formatted_first_check_in.short_description = 'Check In'
    
    def formatted_last_check_out(self, obj):
        if obj.last_check_out:
            return obj.last_check_out.strftime('%H:%M:%S')
        return '-'
    formatted_last_check_out.short_description = 'Check Out'
    
    def status_colored(self, obj):
        colors = {
            'present': 'green',
            'absent': 'red',
            'late': 'orange',
            'early_leave': 'orange',
            'overtime': 'purple',
            'half_day': 'blue',
            'leave': 'teal',
            'holiday': 'gray',
            'weekend': 'gray',
        }
        
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
