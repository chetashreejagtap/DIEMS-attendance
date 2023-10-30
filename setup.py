from account.models import Users
from masters.models import Department, Semester, Class, PracticalBatch
import datetime


def create_superuser():
    user = Users(email="ts.avs.aur@gmail.com", first_name="Tejas", last_name="Solanke", is_superuser=True,
                 is_active=True,is_staff=True,
                 password=""
                 )
    user.set_password("admin")
    user.save()
    print("Super user created successfully")


def create_departments():
    # Create 8 departments with the specified properties
    current_year = datetime.datetime.now().year
    for i in range(1, 9):
        name = f"Department {i}"
        short = f"D{i}"
        academic_year = current_year
        Department.objects.create(name=name, short=short, academic_year=academic_year)
    print("Departments created successfully.")


def create_semesters():
    # Define the number of semesters you want to create
    num_semesters = 8

    # Loop through departments and create semesters for each
    for department_number in range(1, 9):
        department_name = f"Department {department_number}"

        # Get the department instance
        department = Department.objects.get(name=department_name)

        # Create 8 semesters for each department
        for semester_number in range(1, num_semesters + 1):
            sem_year = 1 + (semester_number - 1) // 2
            Semester.objects.create(department=department, sem_year=sem_year, sem_num=semester_number)

    print("Semesters created successfully.")


def create_classes():
    # Define the class names
    class_names = ['A', 'B']

    # Get all semesters
    semesters = Semester.objects.all()

    for semester in semesters:
        for class_name in class_names:
            # Create a class for the semester
            Class.objects.create(sem=semester, name=class_name)

    print("Classes created successfully.")


def create_practical_batches():
    batch_names = ['1', '2', '3', '4', '5']

    classes = Class.objects.all()

    for student_class in classes:
        for batch_name in batch_names:
            PracticalBatch.objects.create(batch_name=f"{student_class.name}{batch_name}", student_class=student_class)

    print("Practical Batches created successfully.")


# Run the functions
create_superuser()
create_departments()
create_semesters()
create_classes()
create_practical_batches()

