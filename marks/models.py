from django.db import models
from masters.models import Student, Subject

# Create your models here.
class Exam_marks(models.Model):
    Student_id =  models.ForeignKey(Student, on_delete=models.SET_NULL, null=True)
    Subject_id = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True)
    Exam_type = models.CharField(max_length=100)
    Exam_marks = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.Subject_id} {self.Exam_type} "