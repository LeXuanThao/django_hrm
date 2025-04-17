from rest_framework import serializers
from .models import (
    WorkMode, EmployeeWorkMode, LeaveType, LeaveRequest, LeaveBalance,
    WorkSchedule, WorkModeOverrideDate, AttendanceRecord, DailyAttendanceSummary
)
from employees.serializers import EmployeeSerializer

class WorkScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    working_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = WorkSchedule
        fields = ['id', 'work_mode', 'day_of_week', 'day_name', 'is_working_day', 
                  'start_time', 'end_time', 'break_start_time', 'break_end_time', 'working_hours']


class WorkModeOverrideDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkModeOverrideDate
        fields = '__all__'


class WorkModeDetailSerializer(serializers.ModelSerializer):
    schedules = WorkScheduleSerializer(many=True, read_only=True)
    override_dates = WorkModeOverrideDateSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkMode
        fields = ['id', 'name', 'code', 'description', 'working_hours_per_day',
                  'working_days_per_week', 'flexible_hours', 'requires_check_in',
                  'break_duration_minutes', 'is_active', 'created_at', 'updated_at',
                  'schedules', 'override_dates']


class WorkModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkMode
        fields = ['id', 'name', 'code', 'description', 'working_hours_per_day',
                  'working_days_per_week', 'flexible_hours', 'requires_check_in',
                  'break_duration_minutes', 'is_active', 'created_at', 'updated_at']


class EmployeeWorkModeSerializer(serializers.ModelSerializer):
    work_mode_details = WorkModeSerializer(source='work_mode', read_only=True)
    
    class Meta:
        model = EmployeeWorkMode
        fields = ['id', 'employee', 'work_mode', 'work_mode_details', 
                  'start_date', 'end_date', 'note', 'created_at', 'updated_at']


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee', read_only=True)
    leave_type_details = LeaveTypeSerializer(source='leave_type', read_only=True)
    approved_by_details = EmployeeSerializer(source='approved_by', read_only=True)
    days_count = serializers.ReadOnlyField()
    
    class Meta:
        model = LeaveRequest
        fields = '__all__'

    def validate(self, data):
        """Kiểm tra tính hợp lệ của đơn nghỉ phép"""
        # Kiểm tra ngày bắt đầu <= ngày kết thúc
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc")
        
        # Kiểm tra số ngày nghỉ còn lại
        if self.context['request'].method in ['POST', 'PUT']:
            employee = data.get('employee')
            leave_type = data.get('leave_type')
            start_date = data.get('start_date')
            
            if employee and leave_type and start_date:
                # Tính số ngày đăng ký
                end_date = data.get('end_date') or start_date
                half_day = data.get('half_day', False)
                
                from datetime import timedelta
                days = (end_date - start_date).days + 1
                if start_date == end_date and half_day:
                    days = 0.5
                
                # Kiểm tra số ngày nghỉ còn lại
                year = start_date.year
                try:
                    balance = LeaveBalance.objects.get(
                        employee=employee, 
                        leave_type=leave_type,
                        year=year
                    )
                    
                    # Nếu cập nhật, loại trừ số ngày của đơn hiện tại
                    used_days = balance.used_days
                    if self.instance:
                        # Loại trừ số ngày của đơn cũ nếu đang cập nhật
                        old_days = self.instance.days_count
                        used_days -= old_days
                    
                    remaining = balance.total_days - used_days
                    if days > remaining:
                        raise serializers.ValidationError(
                            f"Không đủ ngày nghỉ phép. Còn lại: {remaining}, Yêu cầu: {days}"
                        )
                except LeaveBalance.DoesNotExist:
                    # Nếu không có số dư, kiểm tra xem loại nghỉ phép có cho phép nghỉ không giới hạn
                    if leave_type.max_days_per_year > 0:
                        raise serializers.ValidationError("Không có số dư ngày nghỉ phép cho năm này")
        
        return data


class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee', read_only=True)
    leave_type_details = LeaveTypeSerializer(source='leave_type', read_only=True)
    remaining_days = serializers.ReadOnlyField()
    
    class Meta:
        model = LeaveBalance
        fields = '__all__'
        read_only_fields = ('used_days',)


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee', read_only=True)
    record_type_display = serializers.CharField(source='get_record_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = ['id', 'employee', 'employee_details', 'record_date', 'record_time', 
                  'record_type', 'record_type_display', 'status', 'status_display', 
                  'location', 'note', 'is_manual', 'created_at', 'updated_at']
        read_only_fields = ['record_date', 'ip_address', 'device_info', 'created_by']
    
    def create(self, validated_data):
        # Set IP address and device info from request
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self._get_client_ip(request)
            validated_data['device_info'] = request.META.get('HTTP_USER_AGENT', '')
            
            # Set created_by if manual entry
            if validated_data.get('is_manual', False):
                try:
                    validated_data['created_by'] = request.user.employee
                except:
                    pass
        
        return super().create(validated_data)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DailyAttendanceSummarySerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    check_in_time = serializers.SerializerMethodField()
    check_out_time = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyAttendanceSummary
        fields = ['id', 'employee', 'employee_details', 'date', 'first_check_in', 
                  'check_in_time', 'last_check_out', 'check_out_time', 'status', 
                  'status_display', 'total_hours', 'is_complete', 'note', 
                  'created_at', 'updated_at']
        read_only_fields = ['first_check_in', 'last_check_out', 'total_hours', 'is_complete']
    
    def get_check_in_time(self, obj):
        if obj.first_check_in:
            return obj.first_check_in.strftime('%H:%M:%S')
        return None
    
    def get_check_out_time(self, obj):
        if obj.last_check_out:
            return obj.last_check_out.strftime('%H:%M:%S')
        return None