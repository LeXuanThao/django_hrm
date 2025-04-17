from django.db import models
from django.utils import timezone
from employees.models import Employee


class Project(models.Model):
    """Project model for managing company projects"""
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Project Name")
    code = models.CharField(max_length=50, unique=True, verbose_name="Project Code")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    client = models.CharField(max_length=255, blank=True, null=True, verbose_name="Client")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(blank=True, null=True, verbose_name="End Date")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='planning',
        verbose_name="Status"
    )
    priority = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        verbose_name="Priority"
    )
    budget = models.DecimalField(
        max_digits=14, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Budget"
    )
    manager = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='managed_projects',
        verbose_name="Project Manager"
    )
    is_billable = models.BooleanField(default=True, verbose_name="Billable")
    is_internal = models.BooleanField(default=False, verbose_name="Internal Project")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def is_overdue(self):
        if self.end_date and self.status not in ['completed', 'canceled']:
            return self.end_date < timezone.now().date()
        return False
    
    @property
    def progress(self):
        """Calculate project progress based on completed tasks"""
        if self.status == 'completed':
            return 100
        
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        
        completed_tasks = self.tasks.filter(status='completed').count()
        return int((completed_tasks / total_tasks) * 100)


class ProjectMember(models.Model):
    """Model for project team members"""
    ROLE_CHOICES = [
        ('lead', 'Team Lead'),
        ('developer', 'Developer'),
        ('designer', 'Designer'),
        ('tester', 'Tester'),
        ('analyst', 'Business Analyst'),
        ('devops', 'DevOps'),
        ('admin', 'Administrator'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='members',
        verbose_name="Project"
    )
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='project_assignments',
        verbose_name="Employee"
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='developer',
        verbose_name="Role"
    )
    allocation_percentage = models.PositiveSmallIntegerField(
        default=100,
        verbose_name="Allocation (%)",
        help_text="Percentage of time allocated to this project"
    )
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(blank=True, null=True, verbose_name="End Date")
    hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Hourly Rate"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"
        ordering = ['project', 'role', 'employee__id']  # Sử dụng ID là an toàn nhất
        unique_together = ['project', 'employee']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.project.name} ({self.get_role_display()})"
    
    @property
    def is_active(self):
        today = timezone.now().date()
        return (self.start_date <= today and 
                (self.end_date is None or self.end_date >= today))


class Task(models.Model):
    """Task model for project management"""
    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('to_do', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='tasks',
        verbose_name="Project"
    )
    parent_task = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='subtasks',
        verbose_name="Parent Task"
    )
    title = models.CharField(max_length=255, verbose_name="Task Title")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='backlog',
        verbose_name="Status"
    )
    priority = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        verbose_name="Priority"
    )
    assignee = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tasks',
        verbose_name="Assignee"
    )
    created_by = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_tasks',
        verbose_name="Created By"
    )
    start_date = models.DateField(blank=True, null=True, verbose_name="Start Date")
    due_date = models.DateField(blank=True, null=True, verbose_name="Due Date")
    estimated_hours = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Estimated Hours"
    )
    actual_hours = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Actual Hours"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ['priority', 'due_date']
    
    def __str__(self):
        return f"{self.title} ({self.project.name})"
    
    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['completed', 'canceled']:
            return self.due_date < timezone.now().date()
        return False


class TimeEntry(models.Model):
    """Time entry for project tasks"""
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='time_entries',
        verbose_name="Employee"
    )
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='time_entries',
        verbose_name="Project"
    )
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='time_entries',
        null=True, 
        blank=True,
        verbose_name="Task"
    )
    date = models.DateField(verbose_name="Date")
    hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name="Hours"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    billable = models.BooleanField(default=True, verbose_name="Billable")
    approved = models.BooleanField(default=False, verbose_name="Approved")
    approved_by = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_time_entries',
        verbose_name="Approved By"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Time Entry"
        verbose_name_plural = "Time Entries"
        ordering = ['-date', 'employee']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.project.name} - {self.date} ({self.hours}h)"


class OvertimeRequest(models.Model):
    """Overtime request for project work"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled'),
        ('completed', 'Completed'),
    ]
    
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='overtime_requests',
        verbose_name="Employee"
    )
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='overtime_requests',
        verbose_name="Project"
    )
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='overtime_requests',
        null=True, 
        blank=True,
        verbose_name="Task"
    )
    date = models.DateField(verbose_name="Date")
    start_time = models.TimeField(verbose_name="Start Time")
    end_time = models.TimeField(verbose_name="End Time")
    estimated_hours = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        verbose_name="Estimated Hours"
    )
    actual_hours = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Actual Hours"
    )
    reason = models.TextField(verbose_name="Reason for Overtime")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Status"
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        Employee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_overtime_requests',
        verbose_name="Approved By"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Rejection Reason"
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    time_entry = models.OneToOneField(
        TimeEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='overtime_request',
        verbose_name="Related Time Entry"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Overtime Request"
        verbose_name_plural = "Overtime Requests"
        ordering = ['-date', '-requested_at']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.project.name} - {self.date} ({self.estimated_hours}h)"
    
    @property
    def duration_in_hours(self):
        """Calculate overtime duration"""
        if not self.start_time or not self.end_time:
            return 0
            
        import datetime
        start_dt = datetime.datetime.combine(datetime.date.min, self.start_time)
        end_dt = datetime.datetime.combine(datetime.date.min, self.end_time)
        
        # Handle overnight overtime
        if end_dt < start_dt:
            end_dt = datetime.datetime.combine(datetime.date.min + datetime.timedelta(days=1), self.end_time)
            
        duration = end_dt - start_dt
        hours = duration.total_seconds() / 3600
        return round(hours, 2)
    
    def save(self, *args, **kwargs):
        # Auto-calculate estimated hours if not provided
        if not self.estimated_hours:
            self.estimated_hours = self.duration_in_hours
            
        super().save(*args, **kwargs)
    
    def approve(self, approver):
        """Approve the overtime request"""
        if self.status == 'pending':
            from django.utils import timezone
            self.status = 'approved'
            self.approved_by = approver
            self.approved_at = timezone.now()
            self.save()
            return True
        return False
    
    def reject(self, approver, reason):
        """Reject the overtime request"""
        if self.status == 'pending':
            from django.utils import timezone
            self.status = 'rejected'
            self.approved_by = approver
            self.approved_at = timezone.now()
            self.rejection_reason = reason
            self.save()
            return True
        return False
    
    def cancel(self):
        """Cancel the overtime request"""
        if self.status == 'pending':
            self.status = 'canceled'
            self.save()
            return True
        return False
    
    def complete(self, actual_hours=None):
        """Mark overtime as completed and create time entry"""
        if self.status == 'approved':
            from django.utils import timezone
            
            # Update status and completion time
            self.status = 'completed'
            self.completed_at = timezone.now()
            
            # Set actual hours
            if actual_hours is not None:
                self.actual_hours = actual_hours
            else:
                self.actual_hours = self.estimated_hours
            
            # Create time entry if not already created
            if not self.time_entry:
                time_entry = TimeEntry.objects.create(
                    employee=self.employee,
                    project=self.project,
                    task=self.task,
                    date=self.date,
                    hours=self.actual_hours,
                    description=f"Overtime: {self.reason}",
                    billable=True,  # Default to billable, can be configured based on policy
                )
                self.time_entry = time_entry
            
            self.save()
            return True
        return False
    
    @property
    def is_past_due(self):
        """Check if the overtime date is in the past"""
        from django.utils import timezone
        return self.date < timezone.now().date() and self.status == 'pending'


class OvertimePolicy(models.Model):
    """Policy for overtime rates and rules"""
    name = models.CharField(max_length=100, verbose_name="Policy Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    weekday_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=1.5,
        verbose_name="Weekday Rate Multiplier"
    )
    weekend_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=2.0,
        verbose_name="Weekend Rate Multiplier"
    )
    holiday_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=3.0,
        verbose_name="Holiday Rate Multiplier"
    )
    night_rate = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=1.5,
        verbose_name="Night Rate Multiplier"
    )
    night_start_time = models.TimeField(
        default='22:00:00',
        verbose_name="Night Time Start"
    )
    night_end_time = models.TimeField(
        default='06:00:00',
        verbose_name="Night Time End"
    )
    max_daily_hours = models.PositiveSmallIntegerField(
        default=12,
        verbose_name="Maximum Daily Hours"
    )
    max_weekly_hours = models.PositiveSmallIntegerField(
        default=60,
        verbose_name="Maximum Weekly Hours"
    )
    requires_manager_approval = models.BooleanField(
        default=True,
        verbose_name="Requires Manager Approval"
    )
    requires_justification = models.BooleanField(
        default=True,
        verbose_name="Requires Justification"
    )
    min_notice_hours = models.PositiveSmallIntegerField(
        default=24,
        verbose_name="Minimum Notice Hours",
        help_text="Minimum hours of notice required before overtime"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Overtime Policy"
        verbose_name_plural = "Overtime Policies"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def calculate_overtime_rate(self, date, start_time, end_time):
        """Calculate overtime rate based on policy and time"""
        import datetime
        
        # Check if date is a weekend
        is_weekend = date.weekday() >= 5  # 5 = Saturday, 6 = Sunday
        
        # Determine if this is night overtime
        start_dt = datetime.datetime.combine(date, start_time)
        end_dt = datetime.datetime.combine(date, end_time)
        
        # Handle overnight overtime
        if end_dt < start_dt:
            end_dt = datetime.datetime.combine(date + datetime.timedelta(days=1), end_time)
        
        # Check if overtime spans night hours
        night_start = datetime.datetime.combine(date, self.night_start_time)
        night_end = datetime.datetime.combine(date, self.night_end_time)
        
        # Handle night end time on next day
        if night_end < night_start:
            night_end = datetime.datetime.combine(date + datetime.timedelta(days=1), self.night_end_time)
        
        # Check if any part of the overtime period is during night hours
        is_night = (start_dt < night_end and end_dt > night_start)
        
        # Apply rates based on day and time
        if is_weekend:
            return float(self.weekend_rate)
        elif is_night:
            return float(self.night_rate)
        else:
            return float(self.weekday_rate)
