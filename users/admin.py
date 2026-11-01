from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'patronymic', 'is_staff', 'email_verified')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_verified')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'patronymic', 'phone')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональная информация', {'fields': ('username', 'first_name', 'last_name', 'patronymic', 'phone', 'about', 'avatar')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Верификация', {'fields': ('email_verified', 'phone_verified', 'verification_token', 'token_created_at')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'first_name', 'last_name', 'patronymic', 'about', 'avatar'),
        }),
    )

