from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Other URL patterns...
    path('', dashboard, name='dashboard'),
    path('take_attendance/', take_attendance, name='take_attendance'),
    path('upload_attendance/', upload_attendance, name='upload_attendance'),
    path('mark_attendance/', mark_attendance, name='mark_attendance'),
    path('view_attendance/<int:lecture_id>/', view_attendance, name='view_attendance'),
    path('delete_lecture/<int:lecture_id>/', delete_lecture, name='delete_lecture'),
    path('search_by_subject/', search_by_subject, name='search_by_subject'),
    path('class_attendance/', class_attendance, name='class_attendance'),
    path('defaulter', defaulter, name='defaulter'),
    path('success_page/', success_page, name='success_page'),
    path('logout/', logout_view, name='logout_view'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)