from django.contrib import admin
from .models import *


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'total_students', 'total_teachers')

    def total_students(self, obj):
        return Student.objects.filter(department=obj).count()

    total_students.short_description = 'Total Students'  # Display name in the admin panel

    def total_teachers(self, obj):
        return Teacher.objects.filter(department=obj).count()

    total_teachers.short_description = 'Total Teachers'  # Display name in the admin panel


class StudentAdmin(admin.ModelAdmin):
    def get_exclude(self, request, obj=None):
        if obj:  # obj is not None when editing an existing student
            return []
        else:
            return ['department', 'sem']  # Exclude these fields when adding a new student

    list_display = ('first_name', 'last_name', 'batu_prn', 'email', 'student_class', 'department', 'sem')
    list_filter = ('department', 'sem', 'student_class')
    exclude = ('department', 'sem')  # Exclude these fields from the admin

    def department_name(self, obj):
        return obj.department.name
    department_name.short_description = 'Department'

    def sem_year(self, obj):
        return obj.sem.year if obj.sem else ''
    sem_year.short_description = 'Semester Year'

    def student_class_name(self, obj):
        return obj.student_class.name if obj.student_class else ''
    student_class_name.short_description = 'Student Class'


class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'sem')
    list_filter = ('sem',)


class SemesterAdmin(admin.ModelAdmin):
    list_filter = ('department',)


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'subject_type', 'subject_code', 'sem',)


class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'is_present')
    list_filter = ('subject__lecture_date', 'student__student_class', 'subject', 'subject__subject', 'is_present')


class SubjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'sel_class', 'sel_batch', 'subject')
    list_filter = ('teacher', 'sel_class', 'sel_batch', 'subject')
    search_fields = ('teacher__first_name', 'teacher__last_name', 'subject__subject_name')


class LectureTakenAdmin(admin.ModelAdmin):
    list_display = ('subject',)
    list_filter = ('subject',)
    search_fields = ('subject__subject_name',)


admin.site.register(Subject, SubjectAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Teacher)
admin.site.register(Class, ClassAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(PracticalBatch)
admin.site.register(TheoryElective)
admin.site.register(SubjectAssignment, SubjectAssignmentAdmin)
admin.site.register(LectureTaken, LectureTakenAdmin)

