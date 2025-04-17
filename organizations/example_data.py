from organizations.models import Organization, Department, Position, EmployeeContract
from employees.models import Employee
from datetime import date

def create_example_data():
    # Tạo tổ chức
    org1 = Organization.objects.create(
        name="TechCorp",
        address="123 Tech Street, Silicon Valley",
        phone_number="123456789",
        email="contact@techcorp.com"
    )

    org2 = Organization.objects.create(
        name="HealthPlus",
        address="456 Health Avenue, New York",
        phone_number="987654321",
        email="info@healthplus.com"
    )

    # Tạo phòng ban cho tổ chức TechCorp
    dept1 = Department.objects.create(
        organization=org1,
        name="Engineering",
        description="Handles all technical development."
    )

    dept2 = Department.objects.create(
        organization=org1,
        name="Marketing",
        description="Responsible for marketing and outreach."
    )

    # Tạo phòng ban cho tổ chức HealthPlus
    dept3 = Department.objects.create(
        organization=org2,
        name="Research",
        description="Conducts medical research."
    )

    dept4 = Department.objects.create(
        organization=org2,
        name="Customer Support",
        description="Handles customer queries and support."
    )

    # Tạo vị trí cho phòng ban Engineering
    Position.objects.create(
        department=dept1,
        name="Software Engineer",
        description="Develops and maintains software systems."
    )

    Position.objects.create(
        department=dept1,
        name="DevOps Engineer",
        description="Manages infrastructure and deployment."
    )

    # Tạo vị trí cho phòng ban Marketing
    Position.objects.create(
        department=dept2,
        name="Marketing Specialist",
        description="Plans and executes marketing campaigns."
    )

    # Tạo vị trí cho phòng ban Research
    Position.objects.create(
        department=dept3,
        name="Research Scientist",
        description="Conducts experiments and analyzes data."
    )

    # Tạo vị trí cho phòng ban Customer Support
    Position.objects.create(
        department=dept4,
        name="Support Representative",
        description="Provides support to customers."
    )

    # Tạo nhân sự
    employee1 = Employee.objects.create(
        account_id=1,  # Giả sử account_id=1 đã tồn tại
        date_of_birth="1990-01-01",
        hire_date="2020-01-01",
        phone_number="123456789",
        address="123 Employee Street",
        gender="Male",
        job_title="MANAGER"  # Chức danh là Manager
    )

    employee2 = Employee.objects.create(
        account_id=2,  # Giả sử account_id=2 đã tồn tại
        date_of_birth="1992-01-01",
        hire_date="2021-01-01",
        phone_number="987654321",
        address="456 Employee Avenue",
        gender="Female",
        job_title="STAFF"  # Chức danh là Staff
    )

    # Gán nhân sự vào phòng ban
    dept1.employees.add(employee1, employee2)  # Gán cả hai nhân sự vào phòng ban Engineering
    dept2.employees.add(employee2)  # Gán nhân sự thứ hai vào phòng ban Marketing

    # Gán Manager cho phòng ban
    dept1.manager = employee1  # Chỉ nhân viên có job_title là Manager mới được gán
    dept1.save()

    print("Example data with employees and managers added successfully!")

def create_example_contracts():
    employee = Employee.objects.first()  # Giả sử đã có nhân viên trong hệ thống

    EmployeeContract.objects.create(
        employee=employee,
        contract_type='FULL_TIME',
        start_date=date(2023, 1, 1),
        end_date=date(2025, 1, 1),
        salary=50000.00,
        description="Full-time contract for software development."
    )

    EmployeeContract.objects.create(
        employee=employee,
        contract_type='PART_TIME',
        start_date=date(2025, 2, 1),
        salary=20000.00,
        description="Part-time contract for consulting."
    )

    # Hợp đồng thử việc
    EmployeeContract.objects.create(
        employee=employee,
        contract_type='PROBATION',
        start_date=date(2025, 4, 1),
        end_date=date(2025, 6, 30),
        salary=30000.00,
        description="Probation contract for new employee."
    )

    print("Example contracts created successfully!")
    print("Example probation contract created successfully!")