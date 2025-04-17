from django.db import models
from django.utils import timezone
from employees.models import Employee
import datetime

class WorkType(models.Model):
    WORK_TYPE_CHOICES = [
        ('FULL_TIME', 'Full-Time'),
        ('PART_TIME', 'Part-Time'),
        ('INTERNSHIP', 'Internship'),
        ('FREELANCE', 'Freelance'),
    ]

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='work_type')
    work_type = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES)
    description = models.TextField(blank=True)  # Description of work type

    def __str__(self):
        return f"{self.employee} - {self.get_work_type_display()}"


class WorkMode(models.Model):
    """Model for managing employee work modes"""
    name = models.CharField(max_length=100, verbose_name="Mode Name")
    code = models.CharField(max_length=50, unique=True, verbose_name="Mode Code")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    working_hours_per_day = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=8.0,
        help_text="Standard working hours per day",
        verbose_name="Working Hours/Day"
    )
    working_days_per_week = models.PositiveSmallIntegerField(
        default=5,
        help_text="Standard working days per week",
        verbose_name="Working Days/Week"
    )
    flexible_hours = models.BooleanField(
        default=False,
        help_text="Allow employees to have flexible working hours",
        verbose_name="Flexible Hours"
    )
    requires_check_in = models.BooleanField(
        default=True,
        help_text="Require employees to check in",
        verbose_name="Requires Check-in"
    )
    break_duration_minutes = models.PositiveSmallIntegerField(
        default=60,
        help_text="Break time duration in minutes",
        verbose_name="Break Duration (min)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Work Mode"
        verbose_name_plural = "Work Modes"
        ordering = ['name']

    def __str__(self):
        return self.name
        

class WorkSchedule(models.Model):
    """Work schedule for work modes"""
    DAY_CHOICES = (
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday'),
    )
    
    work_mode = models.ForeignKey(
        WorkMode, 
        on_delete=models.CASCADE, 
        related_name='schedules',
        verbose_name="Work Mode"
    )
    day_of_week = models.PositiveSmallIntegerField(
        choices=DAY_CHOICES,
        verbose_name="Day of Week"
    )
    is_working_day = models.BooleanField(
        default=True,
        verbose_name="Working Day"
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Start Time"
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="End Time"
    )
    break_start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Break Start Time"
    )
    break_end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Break End Time"
    )
    
    class Meta:
        verbose_name = "Work Schedule"
        verbose_name_plural = "Work Schedules"
        ordering = ['work_mode', 'day_of_week']
        unique_together = ('work_mode', 'day_of_week')
    
    def __str__(self):
        return f"{self.work_mode.name} - {self.get_day_of_week_display()}"
    
    @property
    def working_hours(self):
        """Calculate total working hours in the day"""
        if not self.is_working_day or not self.start_time or not self.end_time:
            return 0
            
        # Calculate total duration
        total_duration = datetime.datetime.combine(
            datetime.date.min, self.end_time
        ) - datetime.datetime.combine(
            datetime.date.min, self.start_time
        )
        
        # Subtract break time
        if self.break_start_time and self.break_end_time:
            break_duration = datetime.datetime.combine(
                datetime.date.min, self.break_end_time
            ) - datetime.datetime.combine(
                datetime.date.min, self.break_start_time
            )
            total_duration -= break_duration
            
        # Convert to hours
        hours = total_duration.total_seconds() / 3600
        return round(hours, 2)


class WorkModeOverrideDate(models.Model):
    """Special date configuration (holidays, makeup days, etc.)"""
    work_mode = models.ForeignKey(
        WorkMode, 
        on_delete=models.CASCADE, 
        related_name='override_dates',
        verbose_name="Work Mode"
    )
    date = models.DateField(verbose_name="Date")
    is_working_day = models.BooleanField(
        default=False,
        help_text="Mark as working day if it's a makeup day, otherwise a holiday",
        verbose_name="Working Day"
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Description of special day (e.g. National Holiday, Makeup day)",
        verbose_name="Description"
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Start Time"
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="End Time"
    )
    
    class Meta:
        verbose_name = "Special Date"
        verbose_name_plural = "Special Dates"
        ordering = ['date']
        unique_together = ('work_mode', 'date')
    
    def __str__(self):
        status = "Working" if self.is_working_day else "Holiday"
        return f"{self.date} - {status} ({self.work_mode.name})"


class EmployeeWorkMode(models.Model):
    """Model for assigning work modes to employees"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='work_modes')
    work_mode = models.ForeignKey(WorkMode, on_delete=models.CASCADE)
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(blank=True, null=True, verbose_name="End Date")
    note = models.TextField(blank=True, null=True, verbose_name="Note")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Employee Work Mode"
        verbose_name_plural = "Employee Work Modes"
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.work_mode.name}"

    def is_active(self):
        """Check if work mode is currently active"""
        from django.utils import timezone
        today = timezone.now().date()
        return (self.start_date <= today and 
                (self.end_date is None or self.end_date >= today))


class LeaveType(models.Model):
    """Leave type model"""
    name = models.CharField(max_length=100, verbose_name="Name")
    code = models.CharField(max_length=50, unique=True, verbose_name="Code")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    paid = models.BooleanField(default=True, verbose_name="Paid Leave")
    max_days_per_year = models.PositiveIntegerField(default=12, verbose_name="Max Days Per Year")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    require_approval = models.BooleanField(default=True, verbose_name="Requires Approval")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Leave Type"
        verbose_name_plural = "Leave Types"
        ordering = ['name']

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    """Leave request model"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(verbose_name="End Date")
    half_day = models.BooleanField(default=False, verbose_name="Half Day")
    reason = models.TextField(blank=True, null=True, verbose_name="Reason")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    approved_by = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        related_name='approved_leaves',
        null=True, 
        blank=True,
        verbose_name="Approved By"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Rejection Reason")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Leave Request"
        verbose_name_plural = "Leave Requests"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} ({self.start_date} to {self.end_date})"

    @property
    def days_count(self):
        """Calculate number of leave days"""
        if self.start_date == self.end_date:
            return 0.5 if self.half_day else 1
        
        from datetime import timedelta
        delta = self.end_date - self.start_date
        return delta.days + 1


class LeaveBalance(models.Model):
    """Employee's leave balance model"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(verbose_name="Year")
    total_days = models.DecimalField(max_digits=5, decimal_places=1, verbose_name="Total Days")
    used_days = models.DecimalField(max_digits=5, decimal_places=1, default=0, verbose_name="Used Days")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Leave Balance"
        verbose_name_plural = "Leave Balances"
        unique_together = ('employee', 'leave_type', 'year')
        ordering = ['-year']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name} ({self.year})"

    @property
    def remaining_days(self):
        """Calculate remaining leave days"""
        return self.total_days - self.used_days


class AttendanceRecord(models.Model):
    """Employee daily attendance record"""
    RECORD_TYPE_CHOICES = [
        ('check_in', 'Check In'),
        ('check_out', 'Check Out'),
        ('break_start', 'Break Start'),
        ('break_end', 'Break End'),
    ]
    
    STATUS_CHOICES = [
        ('normal', 'Normal'),
        ('late', 'Late'),
        ('early', 'Early Leave'),
        ('overtime', 'Overtime'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
    ]
    
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name="Employee"
    )
    summary = models.ForeignKey(
        'DailyAttendanceSummary',  # Sử dụng string để tránh circular import
        on_delete=models.CASCADE,
        related_name='records',
        null=True,
        blank=True,
        verbose_name="Attendance Summary"
    )
    record_date = models.DateField(
        verbose_name="Record Date",
        default=timezone.now
    )
    record_time = models.DateTimeField(
        verbose_name="Record Time",
        default=timezone.now
    )
    record_type = models.CharField(
        max_length=20,
        choices=RECORD_TYPE_CHOICES,
        verbose_name="Record Type"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='normal',
        verbose_name="Status"
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Location"
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="IP Address"
    )
    device_info = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Device Info"
    )
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Note"
    )
    is_manual = models.BooleanField(
        default=False,
        verbose_name="Manual Entry",
        help_text="Indicates if the record was added manually by admin"
    )
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_attendance_records',
        verbose_name="Created By"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        ordering = ['-record_date', '-record_time']
        indexes = [
            models.Index(fields=['employee', 'record_date']),
            models.Index(fields=['record_date']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.record_date} - {self.get_record_type_display()}"
    
    def save(self, *args, **kwargs):
        # Set the record_date from record_time if not provided
        if not self.record_date and self.record_time:
            self.record_date = self.record_time.date()
            
        # Calculate attendance status based on work schedule
        if self.record_type == 'check_in' and not self.is_manual:
            self._calculate_check_in_status()
        elif self.record_type == 'check_out' and not self.is_manual:
            self._calculate_check_out_status()
            
        super().save(*args, **kwargs)
        
        # Update daily summary after saving attendance record
        DailyAttendanceSummary.objects.update_or_create_from_records(
            self.employee, self.record_date
        )
    
    def _calculate_check_in_status(self):
        """Calculate status for check-in (normal, late)"""
        # Get employee work mode
        work_modes = self.employee.work_modes.filter(
            start_date__lte=self.record_date,
            end_date__isnull=True
        ).order_by('-start_date')
        
        if not work_modes.exists():
            work_modes = self.employee.work_modes.filter(
                start_date__lte=self.record_date,
                end_date__gte=self.record_date
            ).order_by('-start_date')
        
        if not work_modes.exists():
            return
            
        work_mode = work_modes.first().work_mode
        
        # Get day of week (1-7, where 1 is Monday)
        day_of_week = self.record_date.isoweekday()
        
        # Check if there's an override date
        override = WorkModeOverrideDate.objects.filter(
            work_mode=work_mode,
            date=self.record_date
        ).first()
        
        if override:
            if not override.is_working_day:
                self.status = 'normal'  # Not a working day
                return
                
            if override.start_time:
                schedule_start_time = override.start_time
            else:
                schedule_start_time = None
        else:
            # Get regular schedule for this day
            schedule = WorkSchedule.objects.filter(
                work_mode=work_mode,
                day_of_week=day_of_week
            ).first()
            
            if not schedule or not schedule.is_working_day or not schedule.start_time:
                self.status = 'normal'  # Not a working day or no schedule
                return
                
            schedule_start_time = schedule.start_time
        
        if schedule_start_time:
            # Compare check-in time with scheduled start time
            record_time = self.record_time.time()
            
            # Allow grace period (e.g., 10 minutes)
            grace_minutes = 10
            grace_period = datetime.timedelta(minutes=grace_minutes)
            
            schedule_time_with_grace = datetime.datetime.combine(
                datetime.date.min, schedule_start_time
            ) + grace_period
            
            schedule_with_grace = schedule_time_with_grace.time()
            
            if record_time > schedule_with_grace:
                self.status = 'late'
            else:
                self.status = 'normal'
    
    def _calculate_check_out_status(self):
        """Calculate status for check-out (normal, early, overtime)"""
        # Similar to check-in but for check-out time
        # Implementation follows the same pattern as _calculate_check_in_status
        work_modes = self.employee.work_modes.filter(
            start_date__lte=self.record_date,
            end_date__isnull=True
        ).order_by('-start_date')
        
        if not work_modes.exists():
            work_modes = self.employee.work_modes.filter(
                start_date__lte=self.record_date,
                end_date__gte=self.record_date
            ).order_by('-start_date')
        
        if not work_modes.exists():
            return
            
        work_mode = work_modes.first().work_mode
        
        # Get day of week (1-7, where 1 is Monday)
        day_of_week = self.record_date.isoweekday()
        
        # Check if there's an override date
        override = WorkModeOverrideDate.objects.filter(
            work_mode=work_mode,
            date=self.record_date
        ).first()
        
        if override:
            if not override.is_working_day:
                self.status = 'normal'  # Not a working day
                return
                
            if override.end_time:
                schedule_end_time = override.end_time
            else:
                schedule_end_time = None
        else:
            # Get regular schedule for this day
            schedule = WorkSchedule.objects.filter(
                work_mode=work_mode,
                day_of_week=day_of_week
            ).first()
            
            if not schedule or not schedule.is_working_day or not schedule.end_time:
                self.status = 'normal'  # Not a working day or no schedule
                return
                
            schedule_end_time = schedule.end_time
        
        if schedule_end_time:
            # Compare check-out time with scheduled end time
            record_time = self.record_time.time()
            
            # Grace period for early leave (e.g., 10 minutes)
            grace_minutes = 10
            grace_period = datetime.timedelta(minutes=grace_minutes)
            
            schedule_time_with_grace = datetime.datetime.combine(
                datetime.date.min, schedule_end_time
            ) - grace_period
            
            schedule_with_grace = schedule_time_with_grace.time()
            
            # Overtime threshold (e.g., 30 minutes)
            overtime_minutes = 30
            overtime_period = datetime.timedelta(minutes=overtime_minutes)
            
            schedule_time_with_overtime = datetime.datetime.combine(
                datetime.date.min, schedule_end_time
            ) + overtime_period
            
            schedule_with_overtime = schedule_time_with_overtime.time()
            
            if record_time < schedule_with_grace:
                self.status = 'early'
            elif record_time > schedule_with_overtime:
                self.status = 'overtime'
            else:
                self.status = 'normal'


class DailyAttendanceSummaryManager(models.Manager):
    def update_or_create_from_records(self, employee, date):
        """Create or update daily summary from attendance records"""
        # Get all attendance records for the employee on the given date
        records = AttendanceRecord.objects.filter(
            employee=employee,
            record_date=date
        ).order_by('record_time')
        
        # Find first check-in and last check-out
        check_ins = records.filter(record_type='check_in')
        check_outs = records.filter(record_type='check_out')
        
        first_check_in = check_ins.first()
        last_check_out = check_outs.last()
        
        # Calculate total working hours
        total_hours = 0
        if first_check_in and last_check_out:
            total_duration = last_check_out.record_time - first_check_in.record_time
            
            # Subtract break times if available
            break_starts = records.filter(record_type='break_start').order_by('record_time')
            break_ends = records.filter(record_type='break_end').order_by('record_time')
            
            break_periods = list(zip(break_starts, break_ends))
            
            total_break_duration = datetime.timedelta(0)
            for break_start, break_end in break_periods:
                if break_start and break_end:
                    break_duration = break_end.record_time - break_start.record_time
                    total_break_duration += break_duration
            
            total_duration -= total_break_duration
            total_hours = total_duration.total_seconds() / 3600
        
        # Determine overall status
        status = 'present'
        if not first_check_in and not last_check_out:
            status = 'absent'
        elif first_check_in and first_check_in.status == 'late':
            status = 'late'
        elif last_check_out and last_check_out.status == 'early':
            status = 'early_leave'
        elif last_check_out and last_check_out.status == 'overtime':
            status = 'overtime'
        
        # Update or create the summary
        summary, created = self.update_or_create(
            employee=employee,
            date=date,
            defaults={
                'first_check_in': first_check_in.record_time if first_check_in else None,
                'last_check_out': last_check_out.record_time if last_check_out else None,
                'status': status,
                'total_hours': round(total_hours, 2),
                'is_complete': bool(first_check_in and last_check_out)
            }
        )
        
        return summary


class DailyAttendanceSummary(models.Model):
    """Daily summary of employee attendance"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('early_leave', 'Early Leave'),
        ('overtime', 'Overtime'),
        ('half_day', 'Half Day'),
        ('leave', 'On Leave'),
        ('holiday', 'Holiday'),
        ('weekend', 'Weekend'),
    ]
    
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        related_name='attendance_summaries',
        verbose_name="Employee"
    )
    date = models.DateField(verbose_name="Date")
    first_check_in = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="First Check-in"
    )
    last_check_out = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Last Check-out"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='absent',
        verbose_name="Status"
    )
    total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Total Hours"
    )
    is_complete = models.BooleanField(
        default=False,
        verbose_name="Is Complete",
        help_text="Indicates if both check-in and check-out are recorded"
    )
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Note"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = DailyAttendanceSummaryManager()
    
    class Meta:
        verbose_name = "Daily Attendance Summary"
        verbose_name_plural = "Daily Attendance Summaries"
        ordering = ['-date']
        unique_together = ('employee', 'date')
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.date} - {self.get_status_display()}"
