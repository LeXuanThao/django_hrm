from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import (
    WorkMode, EmployeeWorkMode, LeaveType, LeaveRequest, LeaveBalance,
    WorkSchedule, WorkModeOverrideDate, AttendanceRecord, DailyAttendanceSummary
)
from .serializers import (
    WorkModeSerializer, WorkModeDetailSerializer, EmployeeWorkModeSerializer,
    LeaveTypeSerializer, LeaveRequestSerializer, LeaveBalanceSerializer,
    WorkScheduleSerializer, WorkModeOverrideDateSerializer, AttendanceRecordSerializer, DailyAttendanceSummarySerializer
)

# Create your views here.

class WorkModeViewSet(viewsets.ModelViewSet):
    queryset = WorkMode.objects.all()
    serializer_class = WorkModeSerializer
    filterset_fields = ['is_active', 'flexible_hours', 'requires_check_in']
    search_fields = ['name', 'code', 'description']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WorkModeDetailSerializer
        return super().get_serializer_class()
    
    @action(detail=True, methods=['get'])
    def schedules(self, request, pk=None):
        """Lấy lịch làm việc của chế độ làm việc"""
        work_mode = self.get_object()
        schedules = WorkSchedule.objects.filter(work_mode=work_mode)
        serializer = WorkScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def override_dates(self, request, pk=None):
        """Lấy danh sách ngày đặc biệt của chế độ làm việc"""
        work_mode = self.get_object()
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        queryset = WorkModeOverrideDate.objects.filter(work_mode=work_mode)
        
        if year:
            queryset = queryset.filter(date__year=year)
        if month:
            queryset = queryset.filter(date__month=month)
            
        serializer = WorkModeOverrideDateSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def init_default_schedule(self, request, pk=None):
        """Khởi tạo lịch làm việc mặc định (thứ 2-6)"""
        work_mode = self.get_object()
        
        # Xóa lịch hiện tại nếu có
        if request.data.get('reset', False):
            WorkSchedule.objects.filter(work_mode=work_mode).delete()
        
        # Tạo lịch mặc định (thứ 2-6 làm việc, thứ 7-CN nghỉ)
        schedules_created = 0
        
        for day in range(1, 8):
            # Nếu đã tồn tại thì bỏ qua
            if WorkSchedule.objects.filter(work_mode=work_mode, day_of_week=day).exists():
                continue
                
            is_working_day = day <= 5  # Thứ 2-6 là ngày làm việc
            
            # Tạo lịch làm việc
            schedule = WorkSchedule.objects.create(
                work_mode=work_mode,
                day_of_week=day,
                is_working_day=is_working_day,
                start_time='08:00:00' if is_working_day else None,
                end_time='17:00:00' if is_working_day else None,
                break_start_time='12:00:00' if is_working_day else None,
                break_end_time='13:00:00' if is_working_day else None
            )
            schedules_created += 1
        
        return Response({
            'message': f'Đã tạo {schedules_created} lịch làm việc mặc định',
            'schedules_created': schedules_created
        })


class EmployeeWorkModeViewSet(viewsets.ModelViewSet):
    queryset = EmployeeWorkMode.objects.all()
    serializer_class = EmployeeWorkModeSerializer
    filterset_fields = ['employee', 'work_mode', 'start_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'work_mode__name', 'note']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Lọc chế độ làm việc đang áp dụng
        is_active = self.request.query_params.get('is_active')
        if is_active and is_active.lower() == 'true':
            today = timezone.now().date()
            queryset = queryset.filter(
                start_date__lte=today
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=today)
            )
            
        return queryset


class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    filterset_fields = ['is_active', 'paid']
    search_fields = ['name', 'code', 'description']


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    filterset_fields = ['employee', 'leave_type', 'status', 'start_date']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Nếu không phải quản trị viên, chỉ hiển thị đơn của bản thân hoặc cấp dưới
        if not user.is_superuser:
            try:
                employee = user.employee
                queryset = queryset.filter(
                    Q(employee=employee) |  # Đơn của bản thân
                    Q(employee__manager=employee)  # Đơn của nhân viên cấp dưới
                )
            except AttributeError:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Phê duyệt đơn nghỉ phép"""
        leave_request = self.get_object()
        
        # Kiểm tra quyền phê duyệt
        if not request.user.is_superuser:
            try:
                if request.user.employee != leave_request.employee.manager:
                    return Response(
                        {"detail": "Bạn không có quyền phê duyệt đơn này"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except AttributeError:
                return Response(
                    {"detail": "Bạn không có quyền phê duyệt đơn này"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Cập nhật trạng thái
        if leave_request.status != 'pending':
            return Response(
                {"detail": f"Không thể phê duyệt đơn có trạng thái {leave_request.status}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            leave_request.status = 'approved'
            leave_request.approved_by = request.user.employee
            leave_request.approved_at = timezone.now()
            leave_request.save()
            
            # Cập nhật số ngày đã sử dụng
            year = leave_request.start_date.year
            balance, created = LeaveBalance.objects.get_or_create(
                employee=leave_request.employee,
                leave_type=leave_request.leave_type,
                year=year,
                defaults={'total_days': leave_request.leave_type.max_days_per_year}
            )
            
            balance.used_days += leave_request.days_count
            balance.save()
            
            return Response(LeaveRequestSerializer(leave_request).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Từ chối đơn nghỉ phép"""
        leave_request = self.get_object()
        
        # Kiểm tra quyền từ chối
        if not request.user.is_superuser:
            try:
                if request.user.employee != leave_request.employee.manager:
                    return Response(
                        {"detail": "Bạn không có quyền từ chối đơn này"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except AttributeError:
                return Response(
                    {"detail": "Bạn không có quyền từ chối đơn này"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Kiểm tra và lấy lý do từ chối
        rejection_reason = request.data.get('rejection_reason')
        if not rejection_reason:
            return Response(
                {"detail": "Vui lòng cung cấp lý do từ chối"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cập nhật trạng thái
        if leave_request.status != 'pending':
            return Response(
                {"detail": f"Không thể từ chối đơn có trạng thái {leave_request.status}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            leave_request.status = 'rejected'
            leave_request.rejection_reason = rejection_reason
            leave_request.approved_by = request.user.employee
            leave_request.approved_at = timezone.now()
            leave_request.save()
            
            return Response(LeaveRequestSerializer(leave_request).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Hủy đơn nghỉ phép"""
        leave_request = self.get_object()
        
        # Kiểm tra quyền hủy (chỉ người tạo đơn mới có thể hủy)
        if not request.user.is_superuser:
            try:
                if request.user.employee != leave_request.employee:
                    return Response(
                        {"detail": "Bạn không có quyền hủy đơn này"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except AttributeError:
                return Response(
                    {"detail": "Bạn không có quyền hủy đơn này"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Chỉ có thể hủy đơn đang chờ duyệt hoặc đã duyệt
        if leave_request.status not in ['pending', 'approved']:
            return Response(
                {"detail": f"Không thể hủy đơn có trạng thái {leave_request.status}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            old_status = leave_request.status
            leave_request.status = 'canceled'
            leave_request.save()
            
            # Hoàn lại số ngày nghỉ nếu đơn đã được duyệt trước đó
            if old_status == 'approved':
                year = leave_request.start_date.year
                try:
                    balance = LeaveBalance.objects.get(
                        employee=leave_request.employee,
                        leave_type=leave_request.leave_type,
                        year=year
                    )
                    
                    balance.used_days -= leave_request.days_count
                    balance.save()
                except LeaveBalance.DoesNotExist:
                    pass
            
            return Response(LeaveRequestSerializer(leave_request).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LeaveBalanceViewSet(viewsets.ModelViewSet):
    queryset = LeaveBalance.objects.all()
    serializer_class = LeaveBalanceSerializer
    filterset_fields = ['employee', 'leave_type', 'year']
    search_fields = ['employee__first_name', 'employee__last_name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Nếu không phải quản trị viên, chỉ hiển thị số dư của bản thân hoặc cấp dưới
        if not user.is_superuser:
            try:
                employee = user.employee
                queryset = queryset.filter(
                    Q(employee=employee) |  # Số dư của bản thân
                    Q(employee__manager=employee)  # Số dư của nhân viên cấp dưới
                )
            except:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_balances(self, request):
        """Lấy số dư nghỉ phép của bản thân"""
        try:
            employee = request.user.employee
            year = request.query_params.get('year', timezone.now().year)
            
            balances = LeaveBalance.objects.filter(
                employee=employee,
                year=year
            )
            
            serializer = self.get_serializer(balances, many=True)
            return Response(serializer.data)
        except AttributeError:
            return Response(
                {"detail": "Không tìm thấy thông tin nhân viên"}, 
                status=status.HTTP_404_NOT_FOUND
            )


class WorkScheduleViewSet(viewsets.ModelViewSet):
    queryset = WorkSchedule.objects.all()
    serializer_class = WorkScheduleSerializer
    filterset_fields = ['work_mode', 'day_of_week', 'is_working_day']


class WorkModeOverrideDateViewSet(viewsets.ModelViewSet):
    queryset = WorkModeOverrideDate.objects.all()
    serializer_class = WorkModeOverrideDateSerializer
    filterset_fields = ['work_mode', 'is_working_day', 'date']
    search_fields = ['description']


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    filterset_fields = ['employee', 'record_date', 'record_type', 'status', 'is_manual']
    search_fields = ['employee__first_name', 'employee__last_name', 'note', 'location']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(record_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(record_date__lte=end_date)
        
        # Filter for current user's records if not admin
        if not self.request.user.is_superuser:
            try:
                employee = self.request.user.employee
                # Show only their own records or if they're a manager, show their team's records
                queryset = queryset.filter(
                    Q(employee=employee) | 
                    Q(employee__manager=employee)
                )
            except:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def check_in(self, request):
        """Quick endpoint for employee check-in"""
        try:
            employee = request.user.employee
            
            # Check if already checked in today
            today = timezone.now().date()
            existing_check_in = AttendanceRecord.objects.filter(
                employee=employee,
                record_date=today,
                record_type='check_in'
            ).exists()
            
            if existing_check_in:
                return Response(
                    {"detail": "You have already checked in today."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create check-in record
            record = AttendanceRecord(
                employee=employee,
                record_type='check_in',
                location=request.data.get('location', ''),
                note=request.data.get('note', '')
            )
            
            # Get IP and device info
            record.ip_address = self._get_client_ip(request)
            record.device_info = request.META.get('HTTP_USER_AGENT', '')
            
            record.save()
            
            return Response(
                AttendanceRecordSerializer(record).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def check_out(self, request):
        """Quick endpoint for employee check-out"""
        try:
            employee = request.user.employee
            
            # Check if checked in today
            today = timezone.now().date()
            check_in = AttendanceRecord.objects.filter(
                employee=employee,
                record_date=today,
                record_type='check_in'
            ).first()
            
            if not check_in:
                return Response(
                    {"detail": "You need to check in first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if already checked out
            existing_check_out = AttendanceRecord.objects.filter(
                employee=employee,
                record_date=today,
                record_type='check_out'
            ).exists()
            
            if existing_check_out:
                return Response(
                    {"detail": "You have already checked out today."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create check-out record
            record = AttendanceRecord(
                employee=employee,
                record_type='check_out',
                location=request.data.get('location', ''),
                note=request.data.get('note', '')
            )
            
            # Get IP and device info
            record.ip_address = self._get_client_ip(request)
            record.device_info = request.META.get('HTTP_USER_AGENT', '')
            
            record.save()
            
            return Response(
                AttendanceRecordSerializer(record).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def break_start(self, request):
        """Record start of break time"""
        try:
            employee = request.user.employee
            
            # Check if checked in today
            today = timezone.now().date()
            check_in = AttendanceRecord.objects.filter(
                employee=employee,
                record_date=today,
                record_type='check_in'
            ).first()
            
            if not check_in:
                return Response(
                    {"detail": "You need to check in first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create break start record
            record = AttendanceRecord(
                employee=employee,
                record_type='break_start',
                location=request.data.get('location', ''),
                note=request.data.get('note', '')
            )
            
            # Get IP and device info
            record.ip_address = self._get_client_ip(request)
            record.device_info = request.META.get('HTTP_USER_AGENT', '')
            
            record.save()
            
            return Response(
                AttendanceRecordSerializer(record).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def break_end(self, request):
        """Record end of break time"""
        try:
            employee = request.user.employee
            
            # Check if break started
            today = timezone.now().date()
            break_start = AttendanceRecord.objects.filter(
                employee=employee,
                record_date=today,
                record_type='break_start'
            ).order_by('-record_time').first()
            
            if not break_start:
                return Response(
                    {"detail": "You need to start a break first."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if this break already ended
            break_ends_count = AttendanceRecord.objects.filter(
                employee=employee,
                record_date=today,
                record_type='break_end'
            ).count()
            
            break_starts_count = AttendanceRecord.objects.filter(
                employee=employee,
                record_date=today,
                record_type='break_start'
            ).count()
            
            if break_ends_count >= break_starts_count:
                return Response(
                    {"detail": "All breaks are already ended."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create break end record
            record = AttendanceRecord(
                employee=employee,
                record_type='break_end',
                location=request.data.get('location', ''),
                note=request.data.get('note', '')
            )
            
            # Get IP and device info
            record.ip_address = self._get_client_ip(request)
            record.device_info = request.META.get('HTTP_USER_AGENT', '')
            
            record.save()
            
            return Response(
                AttendanceRecordSerializer(record).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DailyAttendanceSummaryViewSet(viewsets.ModelViewSet):
    queryset = DailyAttendanceSummary.objects.all()
    serializer_class = DailyAttendanceSummarySerializer
    filterset_fields = ['employee', 'date', 'status', 'is_complete']
    search_fields = ['employee__first_name', 'employee__last_name', 'note']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filter for current user's records if not admin
        if not self.request.user.is_superuser:
            try:
                employee = self.request.user.employee
                # Show only their own records or if they're a manager, show their team's records
                queryset = queryset.filter(
                    Q(employee=employee) | 
                    Q(employee__manager=employee)
                )
            except:
                queryset = queryset.none()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_attendance(self, request):
        """Get current employee's attendance summary"""
        try:
            employee = request.user.employee
            
            # Default to current month
            today = timezone.now().date()
            start_date = request.query_params.get('start_date', today.replace(day=1))
            end_date = request.query_params.get('end_date', today)
            
            queryset = DailyAttendanceSummary.objects.filter(
                employee=employee,
                date__gte=start_date,
                date__lte=end_date
            ).order_by('-date')
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def team_attendance(self, request):
        """Get attendance summary for manager's team"""
        try:
            employee = request.user.employee
            
            # Default to current date
            date = request.query_params.get('date', timezone.now().date())
            
            team_members = Employee.objects.filter(manager=employee)
            
            queryset = DailyAttendanceSummary.objects.filter(
                employee__in=team_members,
                date=date
            ).order_by('employee__first_name', 'employee__last_name')
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

