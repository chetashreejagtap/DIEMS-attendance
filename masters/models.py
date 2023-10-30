from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100)
    short = models.CharField(max_length=20, unique=True)
    head_of_department = models.ForeignKey('Teacher', on_delete=models.SET_NULL, blank=True, null=True, related_name='department_head')
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    academic_year = models.IntegerField()

    def __str__(self):
        return f"{self.name} {self.academic_year}-{self.academic_year+1}"

    @property
    def student_count(self):
        return Student.objects.filter(department=self).count()

    @property
    def teacher_count(self):
        return Teacher.objects.filter(department=self).count()


class Semester(models.Model):
    YEAR_TYPE_CHOICES = (
        (1, 'FY'),
        (2, 'SY'),
        (3, 'TY'),
        (4, 'Final Yr'),
    )

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    sem_year = models.PositiveSmallIntegerField(choices=YEAR_TYPE_CHOICES)
    sem_num = models.IntegerField()

    def __str__(self):
        return f"Sem {self.sem_num} - {self.get_sem_year_display()} {self.department.name}"


class Teacher(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    thumb_id = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True, null=False)

    # Add other important fields as necessary

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.thumb_id})"


class Class(models.Model):
    sem = models.ForeignKey(Semester, on_delete=models.SET_DEFAULT, default=1)
    name = models.CharField(max_length=50)  # Class name (e.g., Class A, Class B)
    classTeacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        semester_info = f"Year {self.sem.sem_year}, Sem {self.sem.sem_num} - {self.sem.department.academic_year}"
        return f"Class - {self.name}, {semester_info}, {self.sem.department}"


class PracticalBatch(models.Model):
    batch_name = models.CharField(max_length=50)
    student_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.batch_name} : {self.student_class.sem}"


class TheoryElective(models.Model):
    elective_name = models.CharField(max_length=50)
    student_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.elective_name} - {self.student_class.name} {self.student_class.sem}"


class Student(models.Model):
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    sem = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)
    student_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True)
    batch = models.ForeignKey(PracticalBatch, on_delete=models.SET_NULL, blank=True, null=True)
    elective = models.ForeignKey(TheoryElective, on_delete=models.SET_NULL, blank=True, null=True)
    batu_prn = models.CharField(max_length=20, unique=True)
    prn = models.CharField(max_length=10, unique=True)
    roll_no = models.IntegerField(default=0)
    email = models.EmailField(unique=True)
    self_phone_number = models.CharField(max_length=15)
    parents_phone_number = models.CharField(max_length=15)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    address = models.TextField()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.batu_prn})"

    def save(self, *args, **kwargs):
        # Automatically set department and sem based on the selected student_class
        if self.student_class:
            self.department = self.student_class.sem.department
            self.sem = self.student_class.sem
        super().save(*args, **kwargs)


class Subject(models.Model):
    SUBJECT_TYPE_CHOICES = (
        (1, 'Theory'),
        (2, 'Practical'),
        (3, 'Elective'),
        (4, 'Other_Session'),
    )

    subject_id = models.AutoField(primary_key=True)
    subject_name = models.CharField(max_length=50)
    sem = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)
    subject_type = models.PositiveSmallIntegerField(choices=SUBJECT_TYPE_CHOICES)
    subject_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    description = models.TextField()
    att_score = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.subject_name} {self.get_subject_type_display()}"


class SubjectAssignment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    sel_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    sel_batch = models.ForeignKey(PracticalBatch, on_delete=models.CASCADE, null=True, blank=True)
    sel_elective = models.ForeignKey(TheoryElective, on_delete=models.CASCADE, null=True, blank=True)
    total_lectures = models.IntegerField(default=0, null=False)

    def __str__(self):
        return f"{self.teacher} - {self.subject}"


class LectureTaken(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    took_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    class_field = models.ForeignKey(Class, on_delete=models.CASCADE)
    batch_field = models.ForeignKey(PracticalBatch, on_delete=models.CASCADE, null=True, blank=True)
    elective_field = models.ForeignKey(TheoryElective, on_delete=models.CASCADE, null=True, blank=True)
    lecture_date = models.DateField()
    time_slot = models.TimeField()

    def __str__(self):
        return f"Lecture on {self.lecture_date} - {self.subject.subject_name} by {self.took_by.first_name} {self.took_by.last_name}"


class Attendance(models.Model):
    subject = models.ForeignKey(LectureTaken, on_delete=models.CASCADE, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True)
    is_present = models.BooleanField(default=False)
    remark = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.subject.lecture_date} - {self.student.first_name} {self.student.last_name} - {self.subject.subject.subject_name}"


