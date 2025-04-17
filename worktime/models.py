from django.db import models
from employees.models import Employee

class WorkType(models.Model):
    WORK_TYPE_CHOICES = [
        ('FULL_TIME', 'Full-Time'),
        ('PART_TIME', 'Part-Time'),
        ('INTERNSHIP', 'Internship'),
        ('FREELANCE', 'Freelance'),
    ]

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='work_type')
    work_type = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES)
    description = models.TextField(blank=True)  # Mô tả loại hình làm việc

    def __str__(self):
        return f"{self.employee} - {self.get_work_type_display()}"
