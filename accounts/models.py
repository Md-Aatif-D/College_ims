from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class UserManager(BaseUserManager):
    def create_user(self, login_id, password=None, role_name=None):
        if not login_id:
            raise ValueError('Login ID is required')
        
        role = None
        if role_name:
            role, _ = Role.objects.get_or_create(name=role_name)
            
        user = self.model(login_id=login_id, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login_id, password=None):
        user = self.create_user(login_id, password, role_name='principal')
        user.is_admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    # Common auth fields
    login_id = models.CharField(max_length=50, unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')
    
    # Common profile fields (Moved from child tables to satisfy 3NF/BCNF)
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'login_id'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        role_name = self.role.name if self.role else 'None'
        return f"{self.login_id} ({role_name})"

    @property
    def is_staff(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

class PasswordResetRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_requests')
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_resets'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    temp_password = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Reset request for {self.user.login_id} - {self.status}"

class Principal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='principal_profile')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.full_name or self.user.login_id

    @property
    def full_name(self): return self.user.full_name
    @property
    def email(self): return self.user.email
    @property
    def phone(self): return self.user.phone

class VicePrincipal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vp_profile')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.full_name or self.user.login_id

    @property
    def full_name(self): return self.user.full_name
    @property
    def email(self): return self.user.email
    @property
    def phone(self): return self.user.phone

class Manager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='manager_profile')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.full_name or self.user.login_id

    @property
    def full_name(self): return self.user.full_name
    @property
    def email(self): return self.user.email
    @property
    def phone(self): return self.user.phone

class Accountant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='accountant_profile')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.full_name or self.user.login_id

    @property
    def full_name(self): return self.user.full_name
    @property
    def email(self): return self.user.email
    @property
    def phone(self): return self.user.phone

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    qualification = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.full_name or self.user.login_id

    @property
    def full_name(self): return self.user.full_name
    @property
    def email(self): return self.user.email
    @property
    def phone(self): return self.user.phone

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True)
    semester = models.ForeignKey(
        'academics.Semester', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='students'
    )
    is_active = models.BooleanField(default=True)
    enrollment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name or self.user.login_id} ({self.roll_number})"

    @property
    def full_name(self):
        return self.user.full_name

    @property
    def email(self):
        return self.user.email

    @property
    def phone(self):
        return self.user.phone
