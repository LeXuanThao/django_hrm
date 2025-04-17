from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Q
from .models import (
    Project, ProjectMember, Task, TimeEntry,
    OvertimeRequest, OvertimePolicy
)
from .serializers import (
    ProjectSerializer, ProjectMemberSerializer, 
    TaskSerializer, TimeEntrySerializer,
    OvertimeRequestSerializer, OvertimePolicySerializer
)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filterset_fields = ['status', 'priority', 'is_billable', 'is_internal']
    search_fields = ['name', 'code', 'client', 'description']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by manager or project member
        if not self.request.user.is_superuser:
            try:
                employee = self.request.user.employee
                queryset = queryset.filter(
                    Q(manager=employee) | 
                    Q(members__employee=employee)
                ).distinct()
            except AttributeError:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        project = self.get_object()
        members = project.members.all()
        
        is_active = request.query_params.get('is_active')
        if is_active == 'true':
            today = timezone.now().date()
            members = members.filter(
                start_date__lte=today
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=today)
            )
        
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        project = self.get_object()
        tasks = project.tasks.all()
        
        status_param = request.query_params.get('status')
        if status_param:
            tasks = tasks.filter(status=status_param)
        
        assignee_param = request.query_params.get('assignee')
        if assignee_param:
            tasks = tasks.filter(assignee_id=assignee_param)
        
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def time_entries(self, request, pk=None):
        project = self.get_object()
        time_entries = project.time_entries.all()
        
        # Filter by date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            time_entries = time_entries.filter(date__gte=start_date)
        if end_date:
            time_entries = time_entries.filter(date__lte=end_date)
        
        # Filter by employee
        employee_param = request.query_params.get('employee')
        if employee_param:
            time_entries = time_entries.filter(employee_id=employee_param)
        
        # Filter by approval status
        approval_param = request.query_params.get('approved')
        if approval_param in ['true', 'false']:
            time_entries = time_entries.filter(approved=(approval_param == 'true'))
        
        serializer = TimeEntrySerializer(time_entries, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        project = self.get_object()
        
        # Get total hours
        total_hours = project.time_entries.aggregate(total=Sum('hours'))['total'] or 0
        billable_hours = project.time_entries.filter(billable=True).aggregate(total=Sum('hours'))['total'] or 0
        
        # Get task statistics
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(status='completed').count()
        
        # Get member statistics
        active_members = project.members.filter(
            start_date__lte=timezone.now().date()
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=timezone.now().date())
        ).count()
        
        return Response({
            'total_hours': total_hours,
            'billable_hours': billable_hours,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'active_members': active_members,
            'progress': project.progress,
            'is_overdue': project.is_overdue,
            'is_active': project.is_active
        })


class ProjectMemberViewSet(viewsets.ModelViewSet):
    queryset = ProjectMember.objects.all()
    serializer_class = ProjectMemberSerializer
    filterset_fields = ['project', 'role', 'allocation_percentage']
    search_fields = ['employee__first_name', 'employee__last_name', 'notes']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter for current user or project manager
        if not self.request.user.is_superuser:
            try:
                employee = self.request.user.employee
                queryset = queryset.filter(
                    Q(employee=employee) | 
                    Q(project__manager=employee)
                )
            except:
                queryset = queryset.none()
        
        return queryset


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filterset_fields = ['project', 'status', 'priority', 'assignee']
    search_fields = ['title', 'description']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by project manager, task assignee or task creator
        if not self.request.user.is_superuser:
            try:
                employee = self.request.user.employee
                queryset = queryset.filter(
                    Q(project__manager=employee) | 
                    Q(assignee=employee) | 
                    Q(created_by=employee)
                ).distinct()
            except:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        try:
            employee = request.user.employee
            
            status_param = request.query_params.get('status', '')
            tasks = Task.objects.filter(assignee=employee)
            
            if status_param:
                tasks = tasks.filter(status=status_param)
            
            serializer = self.get_serializer(tasks, many=True)
            return Response(serializer.data)
        except AttributeError:
            return Response(
                {"detail": "You don't have associated employee account."},
                status=status.HTTP_400_BAD_REQUEST
            )


class TimeEntryViewSet(viewsets.ModelViewSet):
    queryset = TimeEntry.objects.all()
    serializer_class = TimeEntrySerializer
    filterset_fields = ['project', 'employee', 'date', 'billable', 'approved']
    search_fields = ['description', 'project__name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter for current user, project manager, or approver
        if not self.request.user.is_superuser:
            try:
                employee = self.request.user.employee
                queryset = queryset.filter(
                    Q(employee=employee) | 
                    Q(project__manager=employee)
                ).distinct()
            except:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_entries(self, request):
        try:
            employee = request.user.employee
            
            # Default to current week
            today = timezone.now().date()
            start_of_week = today - timezone.timedelta(days=today.weekday())
            end_of_week = start_of_week + timezone.timedelta(days=6)
            
            start_date = request.query_params.get('start_date', start_of_week)
            end_date = request.query_params.get('end_date', end_of_week)
            
            entries = TimeEntry.objects.filter(
                employee=employee,
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date', 'project')
            
            serializer = self.get_serializer(entries, many=True)
            return Response(serializer.data)
        except:
            return Response(
                {"detail": "You don't have associated employee account."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def bulk_approve(self, request):
        if not request.user.is_superuser:
            try:
                employee = request.user.employee
                entry_ids = request.data.get('entry_ids', [])
                
                if not entry_ids:
                    return Response(
                        {"detail": "No entries specified for approval."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Only allow project managers to approve entries for their projects
                entries = TimeEntry.objects.filter(
                    id__in=entry_ids,
                    project__manager=employee,
                    approved=False
                )
                
                count = 0
                for entry in entries:
                    entry.approved = True
                    entry.approved_by = employee
                    entry.approved_at = timezone.now()
                    entry.save()
                    count += 1
                
                return Response({
                    "detail": f"{count} time entries have been approved."
                })
            except AttributeError:
                return Response(
                    {"detail": "You don't have permission to approve time entries."},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # Superusers can approve any entries
            entry_ids = request.data.get('entry_ids', [])
            
            if not entry_ids:
                return Response(
                    {"detail": "No entries specified for approval."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            entries = TimeEntry.objects.filter(id__in=entry_ids, approved=False)
            
            try:
                employee = request.user.employee
            except:
                employee = None
            
            count = 0
            for entry in entries:
                entry.approved = True
                entry.approved_by = employee
                entry.approved_at = timezone.now()
                entry.save()
                count += 1
            
            return Response({
                "detail": f"{count} time entries have been approved."
            })


class OvertimeRequestViewSet(viewsets.ModelViewSet):
    queryset = OvertimeRequest.objects.all()
    serializer_class = OvertimeRequestSerializer
    filterset_fields = ['employee', 'project', 'status', 'date']
    search_fields = ['employee__first_name', 'employee__last_name', 'project__name', 'reason']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter for current user, project manager
        if not self.request.user.is_superuser:
            try:
                employee = self.request.user.employee
                queryset = queryset.filter(
                    Q(employee=employee) | 
                    Q(project__manager=employee) |
                    Q(employee__manager=employee)
                ).distinct()
            except:
                queryset = queryset.none()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        overtime = self.get_object()
        
        try:
            employee = request.user.employee
            
            # Check permission - must be a manager or project manager
            is_manager = (overtime.employee.manager == employee)
            is_project_manager = (overtime.project.manager == employee)
            
            if is_manager or is_project_manager or request.user.is_superuser:
                if overtime.approve(employee):
                    return Response({"status": "Overtime request approved"})
                else:
                    return Response(
                        {"detail": "Overtime request cannot be approved in its current state."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {"detail": "You don't have permission to approve this overtime request."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except:
            return Response(
                {"detail": "You don't have permission to approve overtime requests."}, 
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        overtime = self.get_object()
        
        try:
            employee = request.user.employee
            reason = request.data.get('reason', '')
            
            if not reason:
                return Response(
                    {"detail": "Rejection reason is required."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check permission - must be a manager or project manager
            is_manager = (overtime.employee.manager == employee)
            is_project_manager = (overtime.project.manager == employee)
            
            if is_manager or is_project_manager or request.user.is_superuser:
                if overtime.reject(employee, reason):
                    return Response({"status": "Overtime request rejected"})
                else:
                    return Response(
                        {"detail": "Overtime request cannot be rejected in its current state."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {"detail": "You don't have permission to reject this overtime request."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except AttributeError:
            return Response(
                {"detail": "You don't have permission to reject overtime requests."}, 
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        overtime = self.get_object()
        
        try:
            employee = request.user.employee
            
            # Only the employee who requested the overtime can cancel it
            if overtime.employee == employee:
                if overtime.cancel():
                    return Response({"status": "Overtime request canceled"})
                else:
                    return Response(
                        {"detail": "Overtime request cannot be canceled in its current state."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {"detail": "You can only cancel your own overtime requests."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except AttributeError:
            return Response(
                {"detail": "Error canceling overtime request."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        overtime = self.get_object()
        
        try:
            employee = request.user.employee
            actual_hours = request.data.get('actual_hours')
            
            if actual_hours:
                try:
                    actual_hours = float(actual_hours)
                except:
                    return Response(
                        {"detail": "Invalid actual hours value."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Check permission - must be the employee or a manager
            is_requester = (overtime.employee == employee)
            is_manager = (overtime.employee.manager == employee)
            is_project_manager = (overtime.project.manager == employee)
            
            if is_requester or is_manager or is_project_manager or request.user.is_superuser:
                if overtime.complete(actual_hours):
                    return Response({"status": "Overtime request completed"})
                else:
                    return Response(
                        {"detail": "Overtime request cannot be completed in its current state."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {"detail": "You don't have permission to complete this overtime request."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except (AttributeError, ValueError):
            return Response(
                {"detail": "Error completing overtime request."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        try:
            employee = request.user.employee
            
            status_param = request.query_params.get('status', '')
            
            # Default to current and future requests
            queryset = OvertimeRequest.objects.filter(employee=employee)
            
            if status_param:
                queryset = queryset.filter(status=status_param)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except:
            return Response(
                {"detail": "You don't have an associated employee account."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        try:
            employee = request.user.employee
            
            # Get all pending overtime requests where user is the manager or project manager
            queryset = OvertimeRequest.objects.filter(
                status='pending'
            ).filter(
                Q(employee__manager=employee) | 
                Q(project__manager=employee)
            ).distinct()
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except:
            return Response(
                {"detail": "You don't have an associated employee account."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def team_requests(self, request):
        try:
            employee = request.user.employee
            
            # Get all overtime requests for team members
            queryset = OvertimeRequest.objects.filter(
                employee__manager=employee
            )
            
            status_param = request.query_params.get('status', '')
            if status_param:
                queryset = queryset.filter(status=status_param)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except:
            return Response(
                {"detail": "You don't have an associated employee account."}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class OvertimePolicyViewSet(viewsets.ModelViewSet):
    queryset = OvertimePolicy.objects.all()
    serializer_class = OvertimePolicySerializer
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        # Non-superusers can only view policies
        if not self.request.user.is_superuser and self.request.method not in permissions.SAFE_METHODS:
            return OvertimePolicy.objects.none()
        return super().get_queryset()
    
    @action(detail=True, methods=['post'])
    def calculate_rate(self, request, pk=None):
        policy = self.get_object()
        
        # Get parameters from request
        try:
            date_str = request.data.get('date')
            start_time_str = request.data.get('start_time')
            end_time_str = request.data.get('end_time')
            
            if not all([date_str, start_time_str, end_time_str]):
                return Response(
                    {"detail": "Date, start time, and end time are required."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            import datetime
            
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.datetime.strptime(start_time_str, '%H:%M:%S').time()
            end_time = datetime.datetime.strptime(end_time_str, '%H:%M:%S').time()
            
            rate = policy.calculate_overtime_rate(date, start_time, end_time)
            
            return Response({
                "rate": rate,
                "date": date_str,
                "start_time": start_time_str,
                "end_time": end_time_str,
            })
        except Exception as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
