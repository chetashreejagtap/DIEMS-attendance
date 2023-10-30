from datetime import datetime, time
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from masters.models import SubjectAssignment, Teacher, LectureTaken, Student, Attendance, Subject, Semester, Class
from .models import Exam_marks


# Create your views here.
@login_required
def addmarks(request):
    context = {'heading': "Take Attendance", 'sub_heading': "Select subject and respective time-slot to mark attendance"}

    teacher_id = Teacher.objects.get(email=request.user.email)

    subject_assignments = SubjectAssignment.objects.filter(teacher=teacher_id).select_related('subject', 'sel_class',
                                                                                              'teacher')
    context["subjects"] = subject_assignments.order_by('subject__subject_type')

    if request.method == 'POST':
        selected_subject_id = request.POST.get('fva-subject')
        selected_exam_name = request.POST.get('fva-exam-name')             
        subject_obj = SubjectAssignment.objects.get(id=selected_subject_id)
        request.session['marks_data'] = {
                'sel_sub': selected_subject_id,
                'sel_exam_type': selected_exam_name,
            }
    
        return redirect('markmarks') 
    return render(request, 'marks/addmarks.html',context)


def get_students_for_subject_assignment(subject_assignment):
    if subject_assignment.subject.subject_type == 1 or subject_assignment.subject.subject_type == 4:
        return Student.objects.filter(student_class=subject_assignment.sel_class)
    elif subject_assignment.subject.subject_type == 2:
        return Student.objects.filter(student_class=subject_assignment.sel_class, batch=subject_assignment.sel_batch)
    elif subject_assignment.subject.subject_type == 3:
        return Student.objects.filter(student_class=subject_assignment.sel_class, elective=subject_assignment.sel_elective)

@login_required
def markmarks(request):
    context = {'heading': "Mark Marks", 'sub_heading': "Mark attendance of the respective students of selected class"}

    marks_data = request.session.get('marks_data')

    if marks_data is not None:
        selected_subject_id = marks_data.get('sel_sub')
        selected_exam_name = marks_data.get('sel_exam_type')

        if selected_subject_id is not None:
            try:
                # Get the subject assignment to determine the class and teacher
                subject_assignment = SubjectAssignment.objects.get(id=selected_subject_id)

                # Get students associated with the selected subject assignment
                students = get_students_for_subject_assignment(subject_assignment)
                context["students"] = students
                context["subject_name"] = subject_assignment.subject

                if request.method == 'POST':
                    for student in students:
                        mark_key = f'mark_{student.id}'
                        mark = request.POST.get(mark_key)
                        
                        
                        # Use the correct field name to get the subject associated with the selected subject ID
                        subject = Subject.objects.get(subject_code=selected_subject_id)
                        

                        # Create an Exam_marks object for each student's mark
                        Exam_marks.objects.create(
                            Student_id=student,
                            Subject_id=subject,
                            Exam_type=selected_exam_name,
                            Exam_marks=mark
                        )

                    # Clear the session data after marking
                    del request.session['marks_data']

                    # Redirect to a success page or any other page
                    return redirect('success_page')  # Replace 'success_page' with the URL name of your success page

            except SubjectAssignment.DoesNotExist:
                context["error"] = "Subject assignment matching query does not exist."
        else:
            context["error"] = "Incomplete or missing lecture data in the session."
    else:
        context["error"] = "Lecture data not found, kindly take attendance again"

    return render(request, 'marks/markmarks.html', context)