from datetime import datetime, time
from django.db import transaction
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from masters.models import SubjectAssignment, Teacher, LectureTaken, Student, Attendance, Subject, Semester, Class

# Create your views here.


@login_required
def dashboard(request):
    context = {'heading': "Dashboard", 'sub_heading': "Welcome to DIETMS Attendance Module"}
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def take_attendance(request):
    context = {'heading': "Take Attendance", 'sub_heading': "Select subject and respective time-slot to mark attendance"}

    teacher_id = Teacher.objects.get(email=request.user.email)

    subject_assignments = SubjectAssignment.objects.filter(teacher=teacher_id).select_related('subject', 'sel_class',
                                                                                              'teacher')
    context["subjects"] = subject_assignments.order_by('subject__subject_type')

    lectures_taken_by_teacher = LectureTaken.objects.filter(took_by=teacher_id).select_related('subject').order_by('-lecture_date')

    # Calculate total present and total absent for each lecture
    for lecture in lectures_taken_by_teacher:
        lecture.total_present = Attendance.objects.filter(subject=lecture, is_present=True).count()
        lecture.total_absent = Attendance.objects.filter(subject=lecture, is_present=False).count()

    # Create a dictionary to keep track of consecutive absent lectures for each student
    student_consecutive_absent = {}

    for lecture in lectures_taken_by_teacher:
        # Retrieve the students who were absent in this lecture
        absent_students = Attendance.objects.filter(subject=lecture, is_present=False).values_list('student', flat=True)

        for student_id in absent_students:
            # Initialize or update the consecutive_absent count for each student
            if student_id not in student_consecutive_absent:
                student_consecutive_absent[student_id] = 1
            else:
                student_consecutive_absent[student_id] += 1

            students_to_highlight = [student_id for student_id, consecutive_absent in student_consecutive_absent.items() if consecutive_absent >= 3]

    context["recent_attendance"] = lectures_taken_by_teacher
    context["students_to_highlight"] = students_to_highlight 

    if request.method == 'POST':
        selected_subject_id = request.POST.get('fva-subject')
        selected_time_slot = request.POST.get('fva-time-slot')
        selected_lecture_date = request.POST.get('fva-lecture-date')

        subject_obj = SubjectAssignment.objects.get(id=selected_subject_id)

        # Check for time slot and date conflict
        existing_lectures = 0
        existing_lectures = LectureTaken.objects.filter(
            subject__sem=subject_obj.subject.sem,
            class_field=subject_obj.sel_class,
            lecture_date=selected_lecture_date,
            time_slot=selected_time_slot
        )

        if existing_lectures:
            if existing_lectures.first().subject.subject_type == 2 and subject_obj.subject.subject_type == 2:
                existing_lectures = LectureTaken.objects.filter(
                    subject__sem=subject_obj.subject.sem,
                    class_field=subject_obj.sel_class,
                    batch_field=subject_obj.sel_batch,
                    lecture_date=selected_lecture_date,
                    time_slot=selected_time_slot
                )
            elif existing_lectures.first().subject.subject_type == 3 and subject_obj.subject.subject_type == 3:
                existing_lectures = LectureTaken.objects.filter(
                    subject__sem=subject_obj.subject.sem,
                    class_field=subject_obj.sel_class,
                    elective_field=subject_obj.sel_elective,
                    lecture_date=selected_lecture_date,
                    time_slot=selected_time_slot
                )

        if existing_lectures:
            conflicting_teacher = existing_lectures.first().took_by
            error_message = f"Time conflict: Attendance already submitted at this time - {selected_time_slot}, by {conflicting_teacher.first_name} {conflicting_teacher.last_name}"
            context["error"] = error_message
            return render(request, 'dashboard/attend/take_attendance.html', context)
        else:
            request.session['lecture_data'] = {
                '1': selected_subject_id,
                '2': selected_time_slot,
                '3': selected_lecture_date
            }

            # Redirect to a new page for marking attendance
            return redirect('mark_attendance')

    return render(request, 'dashboard/attend/take_attendance.html', context)


def get_students_for_subject_assignment(subject_assignment):
    if subject_assignment.subject.subject_type == 1 or subject_assignment.subject.subject_type == 4:
        return Student.objects.filter(student_class=subject_assignment.sel_class)
    elif subject_assignment.subject.subject_type == 2:
        return Student.objects.filter(student_class=subject_assignment.sel_class, batch=subject_assignment.sel_batch)
    elif subject_assignment.subject.subject_type == 3:
        return Student.objects.filter(student_class=subject_assignment.sel_class, elective=subject_assignment.sel_elective)


@login_required
def upload_attendance(request):
    context = {'heading': "Upload Attendance", 'sub_heading': "Upload attendance excel subject wise."}

    teacher_id = Teacher.objects.get(email=request.user.email)

    subject_assignments = SubjectAssignment.objects.filter(teacher=teacher_id).select_related('subject', 'sel_class', 'teacher')
    context["subjects"] = subject_assignments.order_by('subject__subject_type')

    try:
        if request.method == 'POST' and request.FILES['excel_file']:
            excel_file = request.FILES['excel_file']
            subject_id = request.POST.get('fva-subject')  # Get the subject ID from the form

            try:
                subject_assignment = SubjectAssignment.objects.get(pk=subject_id, teacher=teacher_id)
            except SubjectAssignment.DoesNotExist:
                context['error'] = 'Subject Assignment not found'
                return render(request, 'dashboard/attend/upload_attendance.html', context)

            try:
                df = pd.read_excel(excel_file)

                total_lectures = []
                lecture_names = []

                with transaction.atomic():  # Use atomic transaction block
                    # Extract lecture date and time from column names and create LectureTaken rows
                    for col_name in df.columns:
                        if col_name.startswith('lect'):
                            lecture_names.append(col_name)
                            lecture_parts = col_name.split('_')
                            if len(lecture_parts) == 3:
                                lecture_date_str, lecture_time_str = lecture_parts[1], lecture_parts[2]
                                lecture_datetime = datetime.strptime(f"{lecture_date_str} {lecture_time_str}", "%d/%m/%y %H:%M")

                                # Check for time slot and date conflict
                                existing_lectures = LectureTaken.objects.filter(
                                    subject__sem=subject_assignment.subject.sem,
                                    class_field=subject_assignment.sel_class,
                                    lecture_date=lecture_datetime.date(),
                                    time_slot=lecture_datetime.time()
                                )

                                if existing_lectures:
                                    if existing_lectures.first().subject.subject_type == 2 and subject_assignment.subject.subject_type == 2:
                                        existing_lectures = LectureTaken.objects.filter(
                                            subject__sem=subject_assignment.subject.sem,
                                            class_field=subject_assignment.sel_class,
                                            batch_field=subject_assignment.sel_batch,
                                            lecture_date=lecture_datetime.date(),
                                            time_slot=lecture_datetime.time()
                                        )
                                    elif existing_lectures.first().subject.subject_type == 3 and subject_assignment.subject.subject_type == 3:
                                        existing_lectures = LectureTaken.objects.filter(
                                            subject__sem=subject_assignment.subject.sem,
                                            class_field=subject_assignment.sel_class,
                                            elective_field=subject_assignment.sel_elective,
                                            lecture_date=lecture_datetime.date(),
                                            time_slot=lecture_datetime.time()
                                        )

                                    if existing_lectures:
                                        conflicting_teacher = existing_lectures.first().took_by
                                        error_message = f"Time conflict: Attendance already submitted at this time - {lecture_time_str}, by {conflicting_teacher.first_name} {conflicting_teacher.last_name}"
                                        context["error"] = error_message
                                        return render(request, 'dashboard/attend/upload_attendance.html', context)

                                # Create LectureTaken row
                                lecture_taken = LectureTaken.objects.create(
                                    subject=subject_assignment.subject,
                                    took_by=teacher_id,
                                    class_field=subject_assignment.sel_class,
                                    batch_field=subject_assignment.sel_batch,
                                    elective_field=subject_assignment.sel_elective,
                                    lecture_date=lecture_datetime.date(),
                                    time_slot=lecture_datetime.time()
                                )
                                total_lectures.append(lecture_taken)

                    # Fetch students for the selected SubjectAssignment
                    students = get_students_for_subject_assignment(subject_assignment)

                    # Iterate through lectures and add attendance for each student
                    for lecture_name, lecture_taken in zip(lecture_names, total_lectures):
                        for index, row in df.iterrows():
                            roll_no = row['roll_no']  # Adjust this based on your Excel column names
                            student = students.filter(roll_no=roll_no).first()

                            if student:
                                is_present = int(row[lecture_name])  # Assuming 0 for absent, 1 for present

                                # Add attendance for the student for this lecture
                                Attendance.objects.create(
                                    subject=lecture_taken,
                                    student=student,
                                    is_present=is_present
                                )

                return render(request, 'dashboard/attend/success_page.html')
            except Exception as e:
                context['error'] = f'Error processing Excel file: {str(e)}'
                return render(request, 'dashboard/attend/upload_attendance.html', context)

    except Exception as e:
        # Handle the exception and add the error message to the context
        context['error'] = "An error occurred: " + str(e)
        return render(request, 'dashboard/attend/upload_attendance.html', context)

    return render(request, 'dashboard/attend/upload_attendance.html', context)


@login_required
def mark_attendance(request):
    context = {'heading': "Mark Attendance",
               'sub_heading': "Mark attendance of the respective students of selected class"}

    try:
        lecture_data = request.session.get('lecture_data')

        if lecture_data is not None:
            selected_subject_id = lecture_data.get('1')
            selected_time_slot = lecture_data.get('2')
            selected_lecture_date = lecture_data.get('3')

            if selected_subject_id is not None and selected_time_slot is not None and selected_lecture_date is not None:
                # Get the subject assignment to determine the class and teacher
                subject_assignment = SubjectAssignment.objects.get(id=selected_subject_id)

                # Convert the date string to a date object
                lecture_date = datetime.strptime(selected_lecture_date, "%Y-%m-%d").date()

                # Fetch students for the selected SubjectAssignment
                students = get_students_for_subject_assignment(subject_assignment)
                context["students"] = students
                context["subject_name"] = subject_assignment
                context["date"] = lecture_date
                context["time"] = datetime.strptime(selected_time_slot, "%H:%M").strftime("%I:%M %p")

                if request.method == 'POST':
                    # Create a new lecture entry
                    lecture = LectureTaken.objects.create(
                        subject=subject_assignment.subject,
                        took_by=subject_assignment.teacher,
                        class_field=subject_assignment.sel_class,
                        batch_field=subject_assignment.sel_batch,
                        elective_field=subject_assignment.sel_elective,
                        lecture_date=lecture_date,
                        time_slot=selected_time_slot,
                    )
                    context["lecture"] = lecture
                    # Process and save attendance data to the database
                    for student in students:
                        is_present = request.POST.get(f'student_{student.id}') == 'present'
                        remark = request.POST.get(f'remark_{student.id}')
                        Attendance.objects.create(
                            subject=lecture,
                            student=student,
                            is_present=is_present,
                            remark=remark,
                        )

                    # Redirect to a success page or any other page
                    del request.session['lecture_data']
                    return redirect('success_page')  # Replace 'success_page' with the URL name of your success page

            else:
                context["error"] = "Incomplete or missing lecture data in the session."
        else:
            context["error"] = "Lecture data not found, kindly take attendance again"

    except ObjectDoesNotExist:
        context["error"] = "Subject assignment not found."
    except ValueError:
        context["error"] = "Invalid date format in the session."

    return render(request, 'dashboard/attend/mark_attendance.html', context)


@login_required
def view_attendance(request, lecture_id):
    context = {'heading': "View and Edit Attendance", 'sub_heading': "Check or Edit the attendance of any student"}
    lecture = LectureTaken.objects.get(pk=lecture_id)
    attendance_list = Attendance.objects.filter(subject=lecture)

    # Define the target time (10:15:00)
    target_times = [time(10, 15, 0), time(11, 15, 0), time(13, 15, 0), time(14, 15, 0),time(15, 30, 0),time(16, 30, 0)]
    result_time = []

    for target_time in target_times:
        lecture_exists = LectureTaken.objects.filter(
            lecture_date=lecture.lecture_date,
            class_field=lecture.class_field,
            time_slot=target_time
        ).exists()

        # Append 1 or 0 based on lecture existence
        result_time.append(0 if lecture_exists else 1)

    context["r1"] = result_time[0]
    context["r2"] = result_time[1]
    context["r3"] = result_time[2]
    context["r4"] = result_time[3]
    context["r5"] = result_time[4]
    context["r6"] = result_time[5]

    context['time_slot'] = lecture.time_slot

    if request.method == 'POST':
        lecture.time_slot = request.POST.get('fva-time-slot')
        lecture.save()

        # Process and save edited attendance data
        for attendance in attendance_list:
            is_present = request.POST.get(f'student_{attendance.student.id}') == 'present'
            remark = request.POST.get(f'remark_{attendance.student.id}')
            attendance.is_present = is_present
            attendance.remark = remark
            attendance.save()
            context["message"] = "Attendance Saved Successfully"

    context['subject_type'] = lecture.subject.get_subject_type_display()
    context['lecture'] = lecture
    context['attendance_list'] = attendance_list
    return render(request, 'dashboard/attend/view_attendance.html', context)


def delete_lecture(request, lecture_id):
    lecture = LectureTaken.objects.get(id=lecture_id)
    lecture.delete()
    return redirect(take_attendance)


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


def success_page(request):
    context = {'heading': "Success", 'sub_heading': "Kindly check recent attendance tab to confirm submission"}
    return render(request, 'dashboard/attend/success_page.html', context)


def search_by_subject(request):
    context = {'heading': "Search Subject Wise", "sub_heading": "Select Start and End date to fetch the attendance"}

    # Fetch subjects assigned to the currently logged-in teacher
    teacher = request.user.user_obj  # Replace with how you retrieve the currently logged-in teacher
    subject_assignments = SubjectAssignment.objects.filter(teacher=teacher)

    if request.method == 'POST':
        start_date = request.POST.get('startDate')
        end_date = request.POST.get('endDate')
        selected_subject_id = request.POST.get('subject')
        subject_assignment = SubjectAssignment.objects.get(id=selected_subject_id)

        subject = Subject.objects.get(subject_id=subject_assignment.subject.subject_id)
        students = 0

        # Fetch lectures taken for the selected subject within the date range, Order by lecture date
        lectures_taken = LectureTaken.objects.filter(
            subject=subject,
            class_field=subject_assignment.sel_class,
            batch_field=subject_assignment.sel_batch,
            elective_field=subject_assignment.sel_elective,
            lecture_date__range=[start_date, end_date]
        ).order_by('lecture_date')

        if subject_assignment.subject.subject_type == 1 or subject_assignment.subject.subject_type == 4:
            students = Student.objects.filter(student_class=subject_assignment.sel_class)
        elif subject_assignment.subject.subject_type == 2:
            students = Student.objects.filter(student_class=subject_assignment.sel_class,
                                              batch=subject_assignment.sel_batch)
        elif subject_assignment.subject.subject_type == 3:
            students = Student.objects.filter(student_class=subject_assignment.sel_class,
                                              elective=subject_assignment.sel_elective)

        attendances = {}

        for lecture in lectures_taken:
            attendance_records = Attendance.objects.filter(subject=lecture.id)

            lecture_datetime = f"{lecture.time_slot} {lecture.lecture_date.strftime('%d %b %Y')}"

            for attendance_record in attendance_records:
                student_name = f"{attendance_record.student.first_name} {attendance_record.student.middle_name} {attendance_record.student.last_name}"

                if student_name not in attendances:
                    attendances[student_name] = {}

                if lecture_datetime not in attendances[student_name]:
                    attendances[student_name][lecture_datetime] = []

                attendances[student_name][lecture_datetime].append(attendance_record)

        context['attendances'] = attendances
        context["students"] = students
        context["lectures_taken"] = lectures_taken
        context["sel_subject"] = subject
        context["subject_assign"] = subject_assignment
        context["start_date"] = start_date
        context["end_date"] = end_date

    teacher = request.user.user_obj
    subject_assignments = SubjectAssignment.objects.filter(teacher=teacher.id)
    context["subjects"] = subject_assignments
    return render(request, 'dashboard/search/search_by_subject.html', context)


def create_student_groups(students):
    groups = []

    # Create a dictionary to store students by elective and batch
    students_by_elective_batch = {}

    for student in students:
        elective_id = student.elective.id if student.elective else None
        batch_id = student.batch.id if student.batch else None

        key = (elective_id, batch_id)  # Use a tuple as the key

        if key not in students_by_elective_batch:
            students_by_elective_batch[key] = []

        students_by_elective_batch[key].append(student)

    # Convert the dictionary to a list of lists
    for group_students in students_by_elective_batch.values():
        groups.append(group_students)

    return groups


def class_attendance(request):
    context = {
        'heading': 'Search Defaulter Report of a Class',
        'sub_heading': "Select Semester, Class and Batch to display Defaulter List.",
        'semesters': Semester.objects.filter(department_id=request.user.user_obj.department.id)
    }
    group_attendance = []
    if request.method == 'POST':
        selected_class_id = request.POST.get('sel_class')
        # Handle the selected class ID from the form data as needed

        class_obj = Class.objects.get(id=selected_class_id)
        context['class'] = class_obj
        subjects = Subject.objects.filter(sem=class_obj.sem, subject_type__lt=4).order_by('subject_type')
        context['subject_len'] = len(subjects) + 6
        # Get all students belonging to the selected class
        students = Student.objects.filter(student_class_id=selected_class_id)

        # Group students by elective and batch
        students_by_batch = create_student_groups(students)

        for students in students_by_batch:
            attendance_records = []
            total_other_lectures_record = []
            final_at = []
            lectures_all = 0
            for student in students:
                attendance_record = []
                total_other_lectures_record = []
                lectures_all = 0
                present_lectures_all = 0
                for subject in subjects:
                    lectures_taken = 0
                    total_lectures = 0
                    total_present = 0

                    if subject.subject_type == 1:
                        lectures_taken = LectureTaken.objects.filter(subject=subject, class_field=student.student_class)
                        total_lectures = len(lectures_taken)
                    elif subject.subject_type == 2:
                        lectures_taken = LectureTaken.objects.filter(subject=subject, class_field=student.student_class,
                                                                     batch_field=student.batch)
                        total_lectures = len(lectures_taken) * 2
                    elif subject.subject_type == 3:
                        lectures_taken = LectureTaken.objects.filter(subject=subject, class_field=student.student_class,
                                                                     elective_field=student.elective)
                        total_lectures = len(lectures_taken)

                    for lecture in lectures_taken:
                        attendance = Attendance.objects.get(subject=lecture, student=student)
                        if attendance.is_present:
                            total_present += subject.att_score

                    if total_lectures == 0:
                        attendance_record.append(["N/A"])
                        total_other_lectures_record.append(0)
                    else:
                        attendance_record.append([f'{total_present}'])
                        total_other_lectures_record.append(total_lectures)

                    lectures_all += total_lectures
                    present_lectures_all += total_present

                other_subjects = Subject.objects.filter(sem=class_obj.sem, subject_type=4)
                total_other_lectures = 0
                present_other_lectures = 0
                for other_subject in other_subjects:
                    other_lectures_taken = LectureTaken.objects.filter(subject=other_subject,
                                                                       class_field=student.student_class)
                    for other_lecture in other_lectures_taken:
                        total_other_lectures += other_subject.att_score
                        attendance = Attendance.objects.get(subject=other_lecture, student=student)
                        if attendance.is_present:
                            present_other_lectures += other_subject.att_score

                if total_other_lectures == 0:
                    attendance_record.append(["N/A"])
                    context["total_other"] = 0
                else:
                    attendance_record.append([f'{present_other_lectures}'])
                    context["total_other"] = total_other_lectures

                lectures_all += total_other_lectures
                present_lectures_all += present_other_lectures

                if lectures_all == 0:
                    final_attendance = "N/A"  # Handle divide by zero error
                else:
                    attendance_percentage = (present_lectures_all / lectures_all) * 100

                    final_attendance = int(attendance_percentage)

                attendance_record.append([present_lectures_all])
                attendance_record.append([final_attendance])
                final_at.append(final_attendance)
                attendance_records.append(attendance_record)

            combined_data = zip(students, attendance_records, final_at)
            subjects_group = zip(subjects, total_other_lectures_record)
            data = {'attendance_records': combined_data, 'subjects': subjects_group, 'lectures_all': lectures_all}
            group_attendance.append(data)
        context['group_attendance'] = group_attendance
    else:
        students_by_batch = None  # Initialize as None for GET requests

    return render(request, 'dashboard/search/class_attendance.html', context)


def daily_report(request):
    context = {
        'heading': 'Search Daily Report',
        'sub_heading': "Select class and date to display today's attendance reports.",
    }

    user_department_id = request.user.user_obj.department.id
    context['semesters'] = Semester.objects.filter(department_id=user_department_id)

    if request.method == 'POST':
        # Get the selected class and date from the form
        class_id = request.POST.get('fva-class')
        selected_date = request.POST.get('selectedDate')

        # Fetch lecture records for the selected class and date
        lectures = LectureTaken.objects.filter(class_field__id=class_id, lecture_date=selected_date).order_by('time_slot')
        students = Student.objects.filter(student_class__id=class_id)

        attendance_records = []

        for student in students:
            attendance_record = []
            for lecture in lectures:
                try:
                    attendance = Attendance.objects.get(subject=lecture, student=student)
                    if attendance.is_present:
                        attendance_record.append(lecture.subject.att_score)
                    else:
                        attendance_record.append(0)
                except Attendance.DoesNotExist:
                    attendance_record.append("N/A")  # Handle the case when attendance record doesn't exist
            attendance_records.append(attendance_record)
        combined_data = zip(students, attendance_records)
        context["attendance_records"] = combined_data
        context["subjects"] = lectures

    return render(request, 'dashboard/search/daily_report.html', context)


def defaulter(request):
    context = {
        'heading': 'Search Defaulter Report',
        'sub_heading': "Select Semester, Class and Batch to display Defaulter List.",
        'semesters': Semester.objects.filter(department_id=request.user.user_obj.department.id)
    }

    if request.method == "POST":
        class_obj = Class.objects.get(id=request.POST.get('fva-class'))
        students = Student.objects.filter(student_class=class_obj, batch__id=request.POST.get('sel_batch'))

        subjects = Subject.objects.filter(sem=class_obj.sem, subject_type__lt=4).order_by('subject_type')

        attendance_records = []
        total_other_lectures_record = []
        final_at = []
        for student in students:
            attendance_record = []
            total_other_lectures_record = []
            lectures_all = 0
            present_lectures_all = 0
            for subject in subjects:
                lectures_taken = 0
                total_lectures = 0
                total_present = 0

                if subject.subject_type == 1:
                    lectures_taken = LectureTaken.objects.filter(subject=subject, class_field=student.student_class)
                    total_lectures = len(lectures_taken)
                elif subject.subject_type == 2:
                    lectures_taken = LectureTaken.objects.filter(subject=subject, class_field=student.student_class, batch_field=student.batch)
                    total_lectures = len(lectures_taken)*2
                elif subject.subject_type == 3:
                    lectures_taken = LectureTaken.objects.filter(subject=subject, class_field=student.student_class, elective_field=student.elective)
                    total_lectures = len(lectures_taken)

                for lecture in lectures_taken:
                    attendance = Attendance.objects.get(subject=lecture, student=student)
                    if attendance.is_present:
                        total_present += subject.att_score

                if total_lectures == 0:
                    attendance_record.append(["N/A"])
                    total_other_lectures_record.append(0)
                else:
                    attendance_record.append([f'{total_present}'])
                    total_other_lectures_record.append(total_lectures)

                lectures_all += total_lectures
                present_lectures_all += total_present

            other_subjects = Subject.objects.filter(sem=class_obj.sem, subject_type=4)
            total_other_lectures = 0
            present_other_lectures = 0
            for other_subject in other_subjects:
                other_lectures_taken = LectureTaken.objects.filter(subject=other_subject,
                                                                   class_field=student.student_class)
                for other_lecture in other_lectures_taken:
                    total_other_lectures += other_subject.att_score
                    attendance = Attendance.objects.get(subject=other_lecture, student=student)
                    if attendance.is_present:
                        present_other_lectures += other_subject.att_score

            if total_other_lectures == 0:
                attendance_record.append(["N/A"])
                context["total_other"] = 0
            else:
                attendance_record.append([f'{present_other_lectures}'])
                context["total_other"] = total_other_lectures

            lectures_all += total_other_lectures
            present_lectures_all += present_other_lectures

            if lectures_all == 0:
                final_attendance = "N/A"  # Handle divide by zero error
            else:
                attendance_percentage = (present_lectures_all / lectures_all) * 100
                final_attendance = int(attendance_percentage)

            attendance_record.append([final_attendance])
            final_at.append(final_attendance)
            attendance_records.append(attendance_record)

        combined_data = zip(students, attendance_records, final_at)
        context["attendance_records"] = combined_data
        context["subjects"] = zip(subjects, total_other_lectures_record)

    return render(request, 'dashboard/search/defaulter.html', context)