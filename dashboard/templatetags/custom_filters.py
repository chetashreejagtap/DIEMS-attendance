from django import template
from masters.models import Student

register = template.Library()


@register.filter
def get_student_rollno(students, student_name):
    student_name = student_name.split(" ")
    student = students.filter(first_name=student_name[0],middle_name=student_name[1], last_name=student_name[2]).first()
    if student:
        return student.roll_no
    return ""