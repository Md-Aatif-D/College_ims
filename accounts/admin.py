from django.contrib import admin
from .models import (User, Principal, VicePrincipal, Manager, Accountant,
                     Teacher, Student, PasswordResetRequest)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['login_id', 'role', 'is_active', 'must_change_password']
    list_filter = ['role', 'is_active']


@admin.register(Principal)
class PrincipalAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email']


@admin.register(VicePrincipal)
class VPAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email']


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email']


@admin.register(Accountant)
class AccountantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'qualification']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'roll_number', 'semester', 'is_active']
    list_filter = ['semester', 'is_active']


@admin.register(PasswordResetRequest)
class ResetRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'requested_at']
    list_filter = ['status']
