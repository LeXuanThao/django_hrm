from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Project, ProjectMember, Task, TimeEntry, 
    OvertimeRequest, OvertimePolicy
)


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0
    autocomplete_fields = ('employee',)


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ('title', 'status', 'priority', 'assignee', 'due_date', 'estimated_hours')
    autocomplete_fields = ('assignee',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'client', 'status_colored', 'priority_colored', 
                   'start_date', 'end_date', 'manager', 'progress_display', 'is_billable')
    list_filter = ('status', 'priority', 'is_billable', 'is_internal', 'start_date')
    search_fields = ('name', 'code', 'client', 'description', 'manager__first_name', 'manager__last_name')
    date_hierarchy = 'start_date'
    autocomplete_fields = ('manager',)
    readonly_fields = ('progress', 'is_overdue')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'client', 'manager')
        }),
        ('Dates and Status', {
            'fields': ('start_date', 'end_date', 'status', 'priority', 'progress')
        }),
        ('Financial', {
            'fields': ('budget', 'is_billable', 'is_internal')
        }),
    )
    inlines = [ProjectMemberInline, TaskInline]
    
    def status_colored(self, obj):
        colors = {
            'planning': 'blue',
            'active': 'green',
            'on_hold': 'orange',
            'completed': 'purple',
            'canceled': 'red',
        }
        
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    
    def priority_colored(self, obj):
        colors = {
            'low': 'green',
            'medium': 'blue',
            'high': 'orange',
            'urgent': 'red',
        }
        
        color = colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_colored.short_description = 'Priority'
    
    def progress_display(self, obj):
        progress = obj.progress
        color = 'green'
        if progress < 25:
            color = 'red'
        elif progress < 50:
            color = 'orange'
        elif progress < 75:
            color = 'blue'
            
        return format_html(
            '<div style="width:100px; background-color: #f1f1f1; border-radius: 4px;">'
            '<div style="width: {}%; background-color: {}; height: 10px; border-radius: 4px;"></div>'
            '</div> {}%',
            progress, color, progress
        )
    progress_display.short_description = 'Progress'


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('employee', 'project', 'role', 'allocation_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('role', 'project', 'allocation_percentage')
    search_fields = ('employee__first_name', 'employee__last_name', 'project__name')
    autocomplete_fields = ('employee', 'project')
    date_hierarchy = 'start_date'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status_colored', 'priority_colored', 'assignee', 'due_date', 'is_overdue')
    list_filter = ('status', 'priority', 'project')
    search_fields = ('title', 'description', 'assignee__first_name', 'assignee__last_name', 'project__name')
    autocomplete_fields = ('project', 'parent_task', 'assignee', 'created_by')
    date_hierarchy = 'due_date'
    
    def status_colored(self, obj):
        colors = {
            'backlog': 'gray',
            'to_do': 'blue',
            'in_progress': 'orange',
            'review': 'purple',
            'completed': 'green',
            'canceled': 'red',
        }
        
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    
    def priority_colored(self, obj):
        colors = {
            'low': 'green',
            'medium': 'blue',
            'high': 'orange',
            'urgent': 'red',
        }
        
        color = colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_colored.short_description = 'Priority'


class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 0
    fields = ('date', 'hours', 'description', 'billable', 'approved')
    readonly_fields = ('approved',)


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'project', 'task', 'date', 'hours', 'billable', 'approval_status')
    list_filter = ('date', 'billable', 'approved', 'project')
    search_fields = ('employee__first_name', 'employee__last_name', 'project__name', 'description')
    autocomplete_fields = ('employee', 'project', 'task', 'approved_by')
    date_hierarchy = 'date'
    actions = ['approve_entries']
    
    def approval_status(self, obj):
        if obj.approved:
            return format_html(
                '<span style="color: green;">Approved by {} on {}</span>',
                obj.approved_by.full_name if obj.approved_by else 'Unknown',
                obj.approved_at.strftime('%Y-%m-%d %H:%M') if obj.approved_at else 'Unknown'
            )
        return format_html('<span style="color: orange;">Pending</span>')
    approval_status.short_description = 'Approval Status'
    
    def approve_entries(self, request, queryset):
        from django.utils import timezone
        try:
            employee = request.user.employee
            count = 0
            for entry in queryset.filter(approved=False):
                entry.approved = True
                entry.approved_by = employee
                entry.approved_at = timezone.now()
                entry.save()
                count += 1
            
            self.message_user(request, f"{count} time entries have been approved.")
        except:
            self.message_user(request, "You don't have permission to approve time entries.")
    approve_entries.short_description = "Approve selected time entries"


@admin.register(OvertimeRequest)
class OvertimeRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'project', 'task', 'date', 'start_time', 'end_time', 
                    'estimated_hours', 'actual_hours', 'status_colored', 'requested_at')
    list_filter = ('status', 'date', 'project')
    search_fields = ('employee__first_name', 'employee__last_name', 'project__name', 'reason')
    autocomplete_fields = ('employee', 'project', 'task', 'approved_by')
    readonly_fields = ('requested_at', 'approved_at', 'completed_at', 'duration_in_hours')
    date_hierarchy = 'date'
    fieldsets = (
        (None, {
            'fields': ('employee', 'project', 'task', 'date')
        }),
        ('Overtime Details', {
            'fields': ('start_time', 'end_time', 'estimated_hours', 'actual_hours', 'duration_in_hours', 'reason')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_at', 'rejection_reason', 'completed_at')
        }),
        ('Time Entry', {
            'fields': ('time_entry',)
        }),
    )
    actions = ['approve_requests', 'reject_requests', 'complete_requests']
    
    def status_colored(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'blue',
            'rejected': 'red',
            'canceled': 'gray',
            'completed': 'green',
        }
        
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    
    def approve_requests(self, request, queryset):
        from django.utils import timezone
        try:
            employee = request.user.employee
            count = 0
            for ot_request in queryset.filter(status='pending'):
                if ot_request.approve(employee):
                    count += 1
            
            self.message_user(request, f"{count} overtime requests have been approved.")
        except:
            self.message_user(request, "You don't have permission to approve overtime requests.")
    approve_requests.short_description = "Approve selected overtime requests"
    
    def reject_requests(self, request, queryset):
        from django.contrib.admin import helpers
        from django import forms
        from django.http import HttpResponseRedirect
        from django.shortcuts import render
        
        class RejectionForm(forms.Form):
            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            rejection_reason = forms.CharField(
                widget=forms.Textarea,
                required=True,
                label="Reason for rejection"
            )
        
        if 'apply' in request.POST:
            form = RejectionForm(request.POST)
            if form.is_valid():
                rejection_reason = form.cleaned_data['rejection_reason']
                count = 0
                try:
                    employee = request.user.employee
                    for ot_request in queryset.filter(status='pending'):
                        if ot_request.reject(employee, rejection_reason):
                            count += 1
                    
                    self.message_user(request, f"{count} overtime requests have been rejected.")
                    return HttpResponseRedirect(request.get_full_path())
                except:
                    self.message_user(request, "You don't have permission to reject overtime requests.")
                    return HttpResponseRedirect(request.get_full_path())
        else:
            form = RejectionForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        
        return render(request, 'admin/reject_overtime_confirmation.html', {
            'title': "Reject overtime requests",
            'queryset': queryset.filter(status='pending'),
            'form': form,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        })
    reject_requests.short_description = "Reject selected overtime requests"
    
    def complete_requests(self, request, queryset):
        count = 0
        for ot_request in queryset.filter(status='approved'):
            if ot_request.complete():
                count += 1
        
        self.message_user(request, f"{count} overtime requests have been marked as completed.")
    complete_requests.short_description = "Mark selected overtime requests as completed"


@admin.register(OvertimePolicy)
class OvertimePolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'weekday_rate', 'weekend_rate', 'holiday_rate', 
                    'night_rate', 'max_daily_hours', 'max_weekly_hours', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Rate Multipliers', {
            'fields': ('weekday_rate', 'weekend_rate', 'holiday_rate', 'night_rate')
        }),
        ('Night Hours', {
            'fields': ('night_start_time', 'night_end_time')
        }),
        ('Limits & Requirements', {
            'fields': ('max_daily_hours', 'max_weekly_hours', 'min_notice_hours', 
                      'requires_manager_approval', 'requires_justification')
        }),
    )
