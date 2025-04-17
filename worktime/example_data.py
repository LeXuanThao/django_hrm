from worktime.models import WorkType
from employees.models import Employee

def create_example_work_types():
    employee1 = Employee.objects.first()  # Giả sử đã có nhân viên trong hệ thống
    employee2 = Employee.objects.last()

    WorkType.objects.create(
        employee=employee1,
        work_type='FULL_TIME',
        description="Full-time work for software development."
    )

    WorkType.objects.create(
        employee=employee2,
        work_type='PART_TIME',
        description="Part-time work for consulting."
    )

    print("Example work types created successfully!")