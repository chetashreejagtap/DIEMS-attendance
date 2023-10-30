from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Other URL patterns...
    path('', user_login, name='login'),
    path('forgot_password', forgot_pass, name='forgot_password'),
    path('confirm_otp/', confirm_otp, name='confirm_otp'),
    path('change_success', change_success, name='change_success'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)