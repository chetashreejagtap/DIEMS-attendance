# urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

from .views import download_sample_file

urlpatterns = [
    path('upload_student_excel/', views.upload_excel, name='upload_student_excel'),
    path('success_page/', views.upload_success, name='upload_success'),
    path('download-sample/', download_sample_file, name='download_sample_file'),
    path('add_class/', views.add_class, name='add_class'),
    path('delete_class/<int:class_id>/', views.delete_class, name='delete_class'),
    path('display_class/<int:class_id>/', views.display_class, name='display_class'),
    path('add_batch/', views.add_batch, name='add_batch'),
    path('delete_batch/<int:b_id>/', views.delete_batch, name='delete_batch'),
    path('display_batch/<int:b_id>/', views.display_batch, name='display_batch'),
    path('add_elective/', views.add_elective, name='add_elective'),
    path('delete_elective/<int:e_id>/', views.delete_elective, name='delete_elective'),
    path('display_elective/<int:e_id>/', views.display_elective, name='display_elective'),
    path('add_subject/', views.add_subject, name='add_subject'),
    path('delete_subject/<int:s_id>/', views.delete_subject, name='delete_subject'),
    path('display_subject/<int:s_id>/', views.display_subject, name='display_subject'),
    path('assign_subject/', views.assign_subject, name='assign_subject'),
    path('delete_assign_subject/<int:s_id>/', views.delete_assign_subject, name='delete_assign_subject'),
    path('display_assign_subject/<int:s_id>/', views.display_assign_subject, name='display_assign_subject'),
    path('add_student/', views.add_student, name='add_student'),
    path('add_teacher/', views.add_teacher, name='add_teacher'),
    path('edit_teacher/<int:t_id>/', views.edit_teacher, name='edit_teacher'),
    path('delete_teacher/<int:t_id>/', views.delete_teacher, name='delete_teacher'),

    path('display_students/', views.display_students, name='display_students'),
    path('display_subject/<int:t_id>/', views.display_subject, name='display_subject'),
    path('display_subject_type/', views.display_subject_type, name='display_subject_type'),
    path('edit_student/<int:prn>/', views.edit_student, name='edit_student'),
    path('delete_student/<int:prn>/', views.delete_student, name='delete_student'),

    path('get_batches/', views.get_batches, name='get_batches'),
    path('get_electives/', views.get_electives, name='get_electives'),
    path('get_subjects_by_type/', views.get_subjects_by_type, name='get_subjects_by_type'),
    path('get_classes/', views.get_classes, name='get_classes'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
