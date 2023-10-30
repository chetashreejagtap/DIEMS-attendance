import os
import string
import random

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import FileResponse, Http404, JsonResponse, HttpResponseForbidden, HttpResponseNotFound, \
    HttpResponseServerError
from django.shortcuts import render, redirect, get_object_or_404
import pandas as pd
from .models import Student, Teacher, Class, PracticalBatch, TheoryElective, Semester, Subject, SubjectAssignment
from attendance import settings
from django.contrib.auth.decorators import user_passes_test
from account.utils import is_coordinator
from account.models import Users

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.db import transaction


@login_required
@user_passes_test(is_coordinator)
def upload_excel(request):
    context = {
        'heading': "Upload Students Excel",
        'sub_heading': "Add Students using an excel sheet, choose the file and upload to insert the students"
    }

    # Fetch the logged-in teacher based on their email
    user_email = request.user.email
    teacher = Teacher.objects.get(email=user_email)

    # Fetch the department of the teacher
    department = teacher.department

    # Fetch all semester in the department
    department_semesters = Semester.objects.filter(department=department).order_by('sem_num')

    context['department'] = department
    context['semesters'] = department_semesters

    try:
        if request.method == 'POST' and request.FILES['excel_file']:
            excel_file = request.FILES['excel_file']
            selected_class_id = request.POST.get('fva-class')  # Get the selected class ID
            selected_class = Class.objects.get(id=selected_class_id)

            # Start a database transaction
            with transaction.atomic():
                # Assuming the first sheet in the Excel file contains the data
                df = pd.read_excel(excel_file)

                # Loop through the rows of the DataFrame and insert data into the model
                for index, row in df.iterrows():
                    # You can access the department and other related data from 'teacher' and 'department' variables
                    # Example: department.name, teacher.first_name, etc.
                    try:
                        batch_instance = PracticalBatch.objects.get(student_class=selected_class, batch_name=row['batch'])
                    except PracticalBatch.DoesNotExist:
                        batch_instance = None

                    try:
                        elective_instance = TheoryElective.objects.get(student_class=selected_class, elective_name=row['elective'])
                    except TheoryElective.DoesNotExist:
                        elective_instance = None

                    student_data = {
                        'department': department,  # You already have the department from the teacher
                        'sem': selected_class.sem,  # Replace with the correct semester object
                        'student_class': selected_class,  # Replace with the correct class object
                        'batu_prn': row['batu'],
                        'prn': '2021' + str(row['roll_no']),
                        'roll_no': row['roll_no'],
                        'email': row['email'],
                        'self_phone_number': row['phone_no'],
                        'parents_phone_number': row['parents_phone_no'],
                        'first_name': row['fname'],
                        'middle_name': row['mname'],
                        'last_name': row['lname'],
                        'batch': batch_instance,
                        'elective': elective_instance,
                        'address': 'Aurangabad',
                    }

                    # Create a new Student object and save it to the database
                    student = Student(**student_data)
                    student.save()

            return redirect('upload_success')  # Redirect to a success page

    except Exception as e:
        # Handle the exception and add the error message to the context
        context['error'] = "An error occurred: " + str(e)
        return render(request, 'masters/student/upload.html', context)

    return render(request, 'masters/student/upload.html', context)


@login_required
@user_passes_test(is_coordinator)
def upload_success(request):
    context = {'heading': "Success", 'sub_heading': "Kindly check recent class tab to confirm student submission",
               'message': "Students Added Successfully", 'parent': 'upload_student_excel',
               'parent_text': 'Upload Students'}
    return render(request, 'masters/upload_success_page.html', context)


@login_required
@user_passes_test(is_coordinator)
def download_sample_file(request):
    # Path to the sample file in your media directory
    sample_file_path = os.path.join(settings.MEDIA_ROOT, 'sample_file.xlsx')

    # Open and serve the file
    try:
        sample_file = open(sample_file_path, 'rb')
        response = FileResponse(sample_file)
        response['Content-Disposition'] = 'attachment; filename="sample_file.xlsx"'
        return response
    except FileNotFoundError:
        # Handle the case when the sample file is not found
        raise Http404('Sample file not found')


@login_required
@user_passes_test(is_coordinator)
def add_class(request):
    context = {
        'heading': "Add Class",
        'sub_heading': "Create new Class in your Department for your Semester"
    }

    # Fetch semesters for the teacher's department
    teacher_semesters = Semester.objects.filter(department=request.user.user_obj.department)
    department_classes = Class.objects.filter(sem__department=request.user.user_obj.department)

    context['teacher_semesters'] = teacher_semesters
    context['department_classes'] = department_classes

    if request.method == 'POST':
        class_name = request.POST.get('name')
        selected_semester_id = request.POST.get('fva-semester')

        # Get the current teacher's department
        department = request.user.user_obj.department

        try:
            # Fetch the selected semester based on its ID
            selected_semester = Semester.objects.get(id=selected_semester_id, department=department)

            # Check if a class with the same name already exists in the same semester
            if Class.objects.filter(name=class_name, sem=selected_semester).exists():
                error_message = "A class with this name already exists in the selected semester."
                context['error'] = error_message
                return render(request, 'masters/class/add_class.html', context)

            # Create a new class
            new_class = Class(name=class_name, sem=selected_semester)
            new_class.save()
            context['message'] = "Class Added Successfully"
            return render(request, 'masters/class/add_class.html', context)

        except Semester.DoesNotExist:
            error_message = "Selected semester does not exist in your department."
            context['error'] = error_message
            return render(request, 'masters/class/add_class.html', context)
        except IntegrityError:
            error_message = "An error occurred while saving the class."
            context['error'] = error_message
            return render(request, 'masters/class/add_class.html', context)

    return render(request, 'masters/class/add_class.html', context)


@login_required
@user_passes_test(is_coordinator)
def delete_class(request, class_id):
    class_obj = Class.objects.get(id=class_id)
    class_obj.delete()
    return redirect(add_class)


@login_required
@user_passes_test(is_coordinator)
def display_class(request, class_id):
    context = {'heading': "View and Edit Class", 'sub_heading': "Check or Edit the class in your department"}

    try:
        # Get the class object by its ID
        class_item = get_object_or_404(Class, id=class_id)

        if request.method == 'POST':
            # Handle form submission for updating the class
            class_name = request.POST.get('name')
            semester_id = request.POST.get('semester')

            # Check if a class with the same name exists in the selected semester
            existing_class = Class.objects.filter(name=class_name, sem_id=semester_id).exclude(id=class_id).first()

            if existing_class:
                context["error"] = f"A class with the name '{class_name}' already exists in the selected semester."
            else:
                # Update the class object with new data
                class_item.name = class_name
                class_item.sem_id = semester_id
                class_item.save()

                context["message"] = "Class Updated Successfully"

        context['class_item'] = class_item
        context['teacher_semesters'] = Semester.objects.filter(department=request.user.user_obj.department)

    except Exception as e:
        context['error'] = str(e)

    return render(request, 'masters/class/display_class.html', context)


@login_required
@user_passes_test(is_coordinator)
def add_batch(request):
    context = {
        'heading': 'Add Practical Batch',
        'sub_heading': 'Add a new batch to a class.',
    }

    try:
        user_department_id = request.user.user_obj.department.id
        batches = PracticalBatch.objects.filter(student_class__sem__department=user_department_id)

        context['batches'] = batches
        context['semesters'] = Semester.objects.filter(department_id=user_department_id)

        if request.method == 'POST':
            batch_name = request.POST.get('batch_name')
            student_class_id = request.POST.get('fva-class')
            student_class = Class.objects.get(id=student_class_id)

            # Check if a batch with the same name already exists for the selected class
            if PracticalBatch.objects.filter(batch_name=batch_name, student_class=student_class).exists():
                raise IntegrityError(
                    f'A batch with the same name : {batch_name} already exists for this class : {student_class.sem.department.name} Sem {student_class.sem.sem_num}, Div {student_class.name}.')

            batch = PracticalBatch.objects.create(
                batch_name=batch_name,
                student_class=student_class,
            )
            batch.save()
            context['message'] = 'Batch added successfully!'

    except IntegrityError as e:
        context['error'] = str(e)
    except Exception as e:
        context['error'] = str(e)

    return render(request, 'masters/batch/add_batch.html', context)


@login_required
@user_passes_test(is_coordinator)
def delete_batch(request, b_id):
    batch_obj = PracticalBatch.objects.get(id=b_id)
    batch_obj.delete()
    return redirect(add_batch)


@login_required
@user_passes_test(is_coordinator)
def display_batch(request, b_id):
    batch_id = b_id
    context = {
        'heading': 'Display and Edit Batch',
        'sub_heading': 'View and edit batch details.',
    }

    user_department = request.user.user_obj.department
    classes = Class.objects.filter(sem__department=user_department)
    context['classes'] = classes

    batch = PracticalBatch.objects.get(id=batch_id)

    if request.method == 'POST':
        batch_name = request.POST.get('batch_name')
        student_class_id = request.POST.get('student_class')

        try:
            # Check if a batch with the same name exists in the selected class
            existing_batch = PracticalBatch.objects.filter(
                batch_name=batch_name,
                student_class_id=student_class_id
            ).exclude(id=batch_id).first()

            if existing_batch:
                error = f"A batch with the name '{batch_name}' already exists in the selected class."
                context['error'] = error
                context['batch_name'] = batch_name
                context['student_class'] = student_class_id

                return render(request, 'masters/batch/display_batch.html', context)

            # Update the Batch object
            batch.batch_name = batch_name
            batch.student_class_id = student_class_id
            batch.save()

            message = f"Batch '{batch.batch_name}' updated successfully."
            context['message'] = message
            context['batch_name'] = batch_name
            context['student_class'] = student_class_id
            return render(request, 'masters/batch/display_batch.html', context)

        except IntegrityError as e:
            error = f"An error occurred while updating the batch: {str(e)}"
            context['error'] = error
            context['batch_name'] = batch_name
            context['student_class'] = student_class_id
            return render(request, 'masters/batch/display_batch.html', context)

    context['batch_name'] = batch.batch_name
    context['student_class'] = batch.student_class_id
    return render(request, 'masters/batch/display_batch.html', context)


@login_required
@user_passes_test(is_coordinator)
def add_elective(request):
    context = {
        'heading': 'Add Theory Elective',
        'sub_heading': 'View and edit elective details.',
    }

    user_department = request.user.user_obj.department
    semesters = Semester.objects.filter(department=user_department)
    context['semesters'] = semesters

    electives = TheoryElective.objects.filter(student_class__sem__department=request.user.user_obj.department)
    context['electives'] = electives

    if request.method == 'POST':
        elective_name = request.POST.get('elective_name')
        student_class_id = request.POST.get('fva-class')

        try:
            # Check if an elective with the same name exists in the selected class
            existing_elective = TheoryElective.objects.filter(elective_name=elective_name,
                                                              student_class_id=student_class_id).first()

            if existing_elective:
                error = f"An elective with the name '{elective_name}' already exists in the selected class."
                context['error'] = error
                return render(request, 'masters/elective/add_elective.html', context)

            # If no existing elective with the same name, create the Elective object
            elective = TheoryElective(elective_name=elective_name, student_class_id=student_class_id)
            elective.save()

            message = f"Elective '{elective.elective_name}' added successfully."
            context['message'] = message
        except IntegrityError as e:
            error = f"An error occurred while adding the elective: {str(e)}"
            context['error'] = error

    return render(request, 'masters/elective/add_elective.html', context)


@login_required
@user_passes_test(is_coordinator)
def display_elective(request, e_id):
    context = {
        'heading': 'Display and Edit Elective',
        'sub_heading': 'View and edit elective details.',
    }

    user_department = request.user.user_obj.department
    classes = Class.objects.filter(sem__department=user_department)
    context['classes'] = classes

    elective = TheoryElective.objects.get(id=e_id)

    if request.method == 'POST':
        elective_name = request.POST.get('elective_name')
        student_class_id = request.POST.get('student_class')

        try:
            # Check if an elective with the same name exists in the selected class
            existing_elective = TheoryElective.objects.filter(
                elective_name=elective_name,
                student_class_id=student_class_id
            ).exclude(id=e_id).first()

            if existing_elective:
                error = f"An elective with the name '{elective_name}' already exists in the selected class."
                context['error'] = error
                context['elective_name'] = elective_name
                context['student_class'] = student_class_id
                return render(request, 'masters/elective/display_elective.html', context)

            # Update the Elective object
            elective.elective_name = elective_name
            elective.student_class_id = student_class_id
            elective.save()

            message = f"Elective '{elective.elective_name}' updated successfully."
            context['message'] = message
            context['elective_name'] = elective_name
            context['student_class'] = student_class_id
            return render(request, 'masters/elective/display_elective.html', context)

        except IntegrityError as e:
            error = f"An error occurred while updating the elective: {str(e)}"
            context['error'] = error
            context['elective_name'] = elective_name
            context['student_class'] = student_class_id
            return render(request, 'masters/elective/display_elective.html', context)

    context['elective_name'] = elective.elective_name
    context['student_class'] = elective.student_class_id
    return render(request, 'masters/elective/display_elective.html', context)


@login_required
@user_passes_test(is_coordinator)
def delete_elective(request, e_id):
    elective_obj = TheoryElective.objects.get(id=e_id)
    elective_obj.delete()
    return redirect(add_elective)


@login_required
@user_passes_test(is_coordinator)
def add_subject(request):
    context = {
        'heading': 'Add Subjects',
        'sub_heading': 'Add and view subject details.',
    }

    user_department = request.user.user_obj.department
    semesters = Semester.objects.filter(department=user_department)
    context['semesters'] = semesters

    if request.method == 'POST':
        subject_name = request.POST.get('subject_name')
        sem_id = request.POST.get('sem')
        subject_type = request.POST.get('subject_type')
        subject_code = request.POST.get('subject_code')
        description = request.POST.get('description')
        att_score = request.POST.get('att_score')

        try:
            sem = Semester.objects.get(id=sem_id)

            subject = Subject(
                subject_name=subject_name,
                sem=sem,
                subject_type=subject_type,
                subject_code=subject_code,
                description=description,
                att_score=att_score
            )
            subject.save()

            message = f"Subject '{subject.subject_name}' added successfully."
            context['message'] = message

        except IntegrityError as e:
            error = f"An error occurred while adding the subject: {str(e)}"
            context['error'] = error

    subjects = Subject.objects.filter(sem__department=user_department)
    context['subjects'] = subjects

    return render(request, 'masters/subject/add_subject.html', context)


@login_required
@user_passes_test(is_coordinator)
def display_subject(request, s_id):
    context = {
        'heading': 'Display and Edit Subject',
        'sub_heading': 'View and edit subject details.',
    }

    semesters = Semester.objects.filter
    context['semesters'] = semesters

    subject = Subject.objects.get(subject_id=s_id)

    context['subject_name'] = subject.subject_name
    context['sem'] = subject.sem_id

    if request.method == 'POST':
        subject_name = request.POST.get('subject_name')
        sem_id = request.POST.get('sem')
        # Add your validation and subject update logic here

        try:
            # Update the Subject object
            subject.subject_name = subject_name
            subject.sem_id = sem_id
            subject.save()

            message = f"Subject '{subject_name}' updated successfully."
            context['message'] = message

        except Exception as e:
            error = f"An error occurred while updating the subject: {str(e)}"
            context['error'] = error

    return render(request, 'masters/subject/display_subject.html', context)


@login_required
@user_passes_test(is_coordinator)
def delete_subject(request, s_id):
    subject_obj = Subject.objects.get(subject_id=s_id)
    subject_obj.delete()
    return redirect(add_subject)


@login_required
@user_passes_test(is_coordinator)
def assign_subject(request):
    context = {
        'heading': 'Assign Subjects to Teachers',
        'sub_heading': 'Assign subjects to teachers in your department',
    }

    user_department_id = request.user.user_obj.department.id
    context['semesters'] = Semester.objects.filter(department_id=user_department_id)

    if request.method == 'POST':
        # Get data from the POST request
        teacher_id = request.POST.get('teacher')
        subject_id = request.POST.get('subject')
        sel_class_id = request.POST.get('sel_class')
        sel_batch_id = request.POST.get('sel_batch')
        sel_elective_id = request.POST.get('sel_elective')

        try:
            # Create a new SubjectAssignment object
            subject_assignment = SubjectAssignment(
                teacher_id=teacher_id,
                subject_id=subject_id,
                sel_class_id=sel_class_id,
                sel_batch_id=sel_batch_id,
                sel_elective_id=sel_elective_id,
                total_lectures=0
            )
            subject_assignment.save()
            context['message'] = "Subject assigned successfully."
        except Exception as e:
            context['error'] = f'Error assigning subject: {str(e)}'

    # Retrieve necessary data for rendering the assignment form
    teachers = Teacher.objects.filter(department=request.user.user_obj.department)
    subjects = Subject.objects.filter(sem__department=request.user.user_obj.department)
    classes = Class.objects.filter(sem__department=request.user.user_obj.department)
    batches = PracticalBatch.objects.filter(student_class__sem__department=request.user.user_obj.department)
    electives = TheoryElective.objects.filter(student_class__sem__department=request.user.user_obj.department)
    subject_assignments = SubjectAssignment.objects.filter(teacher__department=request.user.user_obj.department)

    context.update({
        'teachers': teachers,
        'subjects': subjects,
        'classes': classes,
        'batches': batches,
        'electives': electives,
        'subject_assignments': subject_assignments,
    })

    return render(request, 'masters/subject/assign_subject.html', context)


@login_required
@user_passes_test(is_coordinator)
def delete_assign_subject(request, s_id):
    assign_subject_obj = SubjectAssignment.objects.get(id=s_id)
    assign_subject_obj.delete()
    return redirect(assign_subject)


@login_required
@user_passes_test(is_coordinator)
def display_assign_subject(request, s_id):
    return redirect(assign_subject)


@login_required
@user_passes_test(is_coordinator)
def add_student(request):
    context = {'heading': 'Add Student', 'sub_heading': 'You can add a Student with the following information:'}

    classes = Class.objects.filter(sem__department=request.user.user_obj.department)
    batches = PracticalBatch.objects.filter(student_class__sem__department=request.user.user_obj.department)
    electives = TheoryElective.objects.filter(student_class__sem__department=request.user.user_obj.department)

    if request.method == 'POST':
        try:
            # Get the form data from the POST request
            student_class = Class.objects.get(id=request.POST.get('student_class'))
            batch = PracticalBatch.objects.get(id=request.POST.get('batch'))
            elective = TheoryElective.objects.get(id=request.POST.get('elective'))
            batu_prn = request.POST.get('batu_prn')
            prn = request.POST.get('prn')
            roll_no = request.POST.get('roll_no')
            email = request.POST.get('email')
            self_phone_number = request.POST.get('self_phone_number')
            parents_phone_number = request.POST.get('parents_phone_number')
            first_name = request.POST.get('first_name')
            middle_name = request.POST.get('middle_name')
            last_name = request.POST.get('last_name')
            address = request.POST.get('address')

            # Check if the roll_no already exists for this class
            if Student.objects.filter(student_class=student_class, roll_no=roll_no).exists():
                raise ValidationError("A student with the same roll_no already exists in this class.")

            # Create a new Student instance and save it
            student = Student(
                department=request.user.user_obj.department,
                sem=student_class.sem,
                student_class=student_class,
                batch=batch,
                elective=elective,
                batu_prn=batu_prn,
                prn=prn,
                roll_no=roll_no,
                email=email,
                self_phone_number=self_phone_number,
                parents_phone_number=parents_phone_number,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                address=address
            )
            student.save()

            context['message'] = "Student added successfully."

        except Exception as e:
            context['error'] = f"An error occurred: {e}"

    context.update({
        'classes': classes,
        'batches': batches,
        'electives': electives,
        # Add any additional context data you need for the template here
    })

    return render(request, 'masters/student/add_student.html', context)


@login_required
@user_passes_test(is_coordinator)
def add_teacher(request):
    context = {'heading': 'Add Teacher', 'sub_heading': 'You can add a Teacher with the following information:'}

    if request.method == 'POST':
        try:
            # Get data from POST request
            thumb_id = request.POST.get('thumb_id')
            first_name = request.POST.get('first_name')
            middle_name = request.POST.get('middle_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')

            # Create a Teacher object
            teacher = Teacher.objects.create(
                department=request.user.user_obj.department,
                thumb_id=thumb_id,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                email=email,
            )
            teacher.save()

            # Create a random password for the user
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            # Create a User object
            user = Users.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_obj=teacher,
            )
            user.save()

            email_subject = 'Welcome to Diems Attendance'
            email_body = render_to_string('email/account_created.html', {'username': email, 'password': password})
            text_content = strip_tags(email_body)

            email = EmailMultiAlternatives(email_subject, text_content, settings.EMAIL_HOST_USER, [user.email])

            email.attach_alternative(email_body, "text/html")
            email.send()

            context['message'] = 'Teacher added successfully, email has been sent!'

        except IntegrityError:
            context['error'] = 'Teacher with this email or thumb_id already exists'
        except Exception as e:
            context['error'] = f'An error occurred: {str(e)}'
    context['teachers'] = Teacher.objects.filter(department=request.user.user_obj.department)
    return render(request, 'masters/teacher/add_teacher.html', context)


@login_required
@user_passes_test(is_coordinator)
def edit_teacher(request, t_id):
    context = {'heading': 'Edit Teacher'}

    # Retrieve the teacher object based on teacher_id
    teacher = get_object_or_404(Teacher, id=t_id)

    if request.method == 'POST':
        try:
            # Get data from POST request
            # Update the teacher's data
            teacher.thumb_id = request.POST.get('thumb_id')
            teacher.first_name = request.POST.get('first_name')
            teacher.middle_name = request.POST.get('middle_name')
            teacher.last_name = request.POST.get('last_name')
            teacher.email = request.POST.get('email')
            teacher.save()
            context['message'] = 'Data Updated Successfully..!'

            # Redirect to a success page or teacher list
            return redirect('teacher_list')
        except Exception as e:
            context['error'] = f'An error occurred: {str(e)}'

    context['teacher'] = teacher
    return render(request, 'masters/teacher/edit_teacher.html', context)


@login_required
@user_passes_test(is_coordinator)
def delete_teacher(request, t_id):
    try:
        teacher_obj = Teacher.objects.get(id=t_id)

        # Check if the logged-in user's email matches the teacher's email
        if request.user.email == teacher_obj.email:
            return HttpResponseForbidden("You are not allowed to delete your own teacher account.")

        # Check if a user with the same email as the teacher exists
        try:
            user_obj = Users.objects.get(email=teacher_obj.email)
            user_obj.delete()

        except Users.DoesNotExist:
            pass  # User does not exist, no need to delete
        teacher_obj.delete()
        return redirect(add_teacher)

    except Teacher.DoesNotExist:
        return HttpResponseNotFound("Teacher not found")

    except Exception as e:
        return HttpResponseServerError(f"An error occurred: {str(e)}")


@login_required
@user_passes_test(is_coordinator)
def display_subject_type(request):
    context = {
        'heading': 'Display Subject According to Sem and Type',
        'sub_heading': 'View subject details.',
    }
    user_department_id = request.user.user_obj.department.id
    context['semesters'] = Semester.objects.filter(department_id=user_department_id)

    if request.method == 'POST':
        stu_sem = request.POST.get('sem')
        sub_type = request.POST.get('subject_type')
        subjects = Subject.objects.filter(sem=stu_sem, subject_type=sub_type)
        context['subjects'] = subjects
    return render(request, 'masters/subject/display_subject_type.html', context)


@login_required
@user_passes_test(is_coordinator)
def display_students(request):
    context = {
        'heading': 'Display Students',
        'sub_heading': 'Display Student List..!',
    }

    user_department_id = request.user.user_obj.department.id
    context['semesters'] = Semester.objects.filter(department_id=user_department_id)

    if request.method == 'POST':
        student_data = request.POST.get('fva-class')
        student_semester = request.POST.get('fva-semester')
        student_details = Student.objects.filter(student_class=student_data, sem=student_semester)
        # print(student_details[0].roll_no)
        context['student_details_info'] = student_details

    return render(request, 'masters/student/display_students.html', context)


@login_required
@user_passes_test(is_coordinator)
def edit_student(request, prn):
    context = {'heading': 'Edit Student'}

    # Retrieve the student object based on prn (assuming prn is a unique identifier)
    student = get_object_or_404(Student, prn=prn)

    if request.method == 'POST':
        try:
            student.batu_prn = request.POST.get('batu_prn')
            student.prn = request.POST.get('prn')
            student.roll_no = request.POST.get('roll_no')
            student.email = request.POST.get('email')
            student.self_phone_number = request.POST.get('self_phone_number')
            student.parents_phone_number = request.POST.get('parents_phone_number')
            student.first_name = request.POST.get('first_name')
            student.middle_name = request.POST.get('middle_name')
            student.last_name = request.POST.get('last_name')
            student.address = request.POST.get('address')

            student.save()
            context['message'] = 'Data Updated Successfully..!'

            # Redirect to a success page or student list
            return redirect('student_list')
        except Exception as e:
            context['error'] = f'An error occurred: {str(e)}'

    context['student'] = student
    return render(request, 'masters/student/edit_student.html', context)


@login_required
@user_passes_test(is_coordinator)
def display_students(request):
    context = {
        'heading': 'Display Students',
        'sub_heading': 'Display Student List..!',
    }

    user_department_id = request.user.user_obj.department.id
    context['semesters'] = Semester.objects.filter(department_id=user_department_id)

    if request.method == 'POST':
        student_data = request.POST.get('fva-class')
        student_semester = request.POST.get('fva-semester')
        student_details = Student.objects.filter(student_class=student_data, sem=student_semester)
        # print(student_details[0].roll_no)
        context['student_details_info'] = student_details

    return render(request, 'masters/student/display_students.html', context)


@login_required
@user_passes_test(is_coordinator)
def delete_student(request, prn):
    stu_obj = Student.objects.get(prn=prn)
    stu_obj.delete()
    return redirect(display_students)


@login_required
def get_batches(request):
    class_id = request.GET.get('class_id')
    batches = PracticalBatch.objects.filter(student_class_id=class_id).values('id', 'batch_name')
    return JsonResponse({'batches': list(batches)})


@login_required
def get_electives(request):
    class_id = request.GET.get('class_id')
    electives = TheoryElective.objects.filter(student_class_id=class_id).values('id', 'elective_name')
    return JsonResponse({'electives': list(electives)})


@login_required
def get_subjects_by_type(request):
    subject_type = request.GET.get('subject_type')
    semester_id = request.GET.get('semester_id')

    # Filter subjects by both subject_type and semester_id
    subjects = Subject.objects.filter(subject_type=subject_type, sem_id=semester_id).values('subject_id',
                                                                                            'subject_name')

    return JsonResponse({'subjects': list(subjects)})


@login_required
def get_classes(request):
    sem_id = request.GET.get('sem_id')

    # Assuming sem_id is an integer, you can convert it to an int
    try:
        sem_id = int(sem_id)
    except ValueError:
        return JsonResponse({'error': 'Invalid semester ID'}, status=400)

    # Retrieve classes based on the selected semester
    classes = Class.objects.filter(sem__id=sem_id).order_by('name')

    # Serialize the classes to JSON
    classes_list = [{'id': cls.id, 'name': cls.name} for cls in classes]

    return JsonResponse({'classes': classes_list}, safe=False)