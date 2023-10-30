from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Other URL patterns...
    path('addmarks/', views.addmarks, name='addmarks'),
    path('markmarks/', views.markmarks, name='markmarks'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)