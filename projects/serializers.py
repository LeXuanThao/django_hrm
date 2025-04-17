from rest_framework import serializers
from .models import (
    Project, ProjectMember, Task, TimeEntry,
    OvertimeRequest, OvertimePolicy
)
from employees.serializers import EmployeeSerializer


class ProjectSerializer(serializers.ModelSerializer):
    manager_details = EmployeeSerializer(source='manager', read_only=True)
    progress = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = Project
        fields = '__all__'


class ProjectMemberSerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee', read_only=True)
    project_details = ProjectSerializer(source='project', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = ProjectMember
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    assignee_details = EmployeeSerializer(source='assignee', read_only=True)
    created_by_details = EmployeeSerializer(source='created_by', read_only=True)
    project_details = ProjectSerializer(source='project', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Task
        fields = '__all__'


class TimeEntrySerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee', read_only=True)
    project_details = ProjectSerializer(source='project', read_only=True)
    task_details = TaskSerializer(source='task', read_only=True)
    approved_by_details = EmployeeSerializer(source='approved_by', read_only=True)
    
    class Meta:
        model = TimeEntry
        fields = '__all__'
        read_only_fields = ('approved', 'approved_by', 'approved_at')


class OvertimeRequestSerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee', read_only=True)
    project_details = ProjectSerializer(source='project', read_only=True)
    task_details = TaskSerializer(source='task', read_only=True)
    approved_by_details = EmployeeSerializer(source='approved_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_in_hours = serializers.ReadOnlyField()
    is_past_due = serializers.ReadOnlyField()
    
    class Meta:
        model = OvertimeRequest
        fields = '__all__'
        read_only_fields = ('approved_by', 'approved_at', 'completed_at', 'time_entry')


class OvertimePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = OvertimePolicy
        fields = '__all__'