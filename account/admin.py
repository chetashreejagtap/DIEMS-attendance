from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Users


class CustomUserAdmin(UserAdmin):

    list_display = ('email', 'user_obj', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'user_obj')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_coordinator')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser')}
        ),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


admin.site.register(Users, CustomUserAdmin)