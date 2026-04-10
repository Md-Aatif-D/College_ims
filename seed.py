"""
IMS Seed Data Script
Creates initial Principal + demo accounts for testing
Run: python seed.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_backend.settings')
django.setup()

from accounts.models import User, Role, Principal, VicePrincipal, Manager, Accountant, Teacher

def create_if_not_exists(login_id, role_name, full_name, email, password='Welcome@123'):
    r, _ = Role.objects.get_or_create(name=role_name)
    user, created = User.objects.get_or_create(
        login_id=login_id, 
        defaults={
            'role': r, 
            'must_change_password': False,
            'full_name': full_name,
            'email': email
        }
    )
    if created:
        user.set_password(password)
        user.save()
        print(f"✅ Created {role_name}: {login_id} / {password}")
    else:
        print(f"⚠️  Already exists: {login_id}")
    return user, created

print("\n🎓 IMS — Seeding initial data...\n")

# Principal
u, c = create_if_not_exists('PRINCIPAL01', 'principal', 'Dr. Rajesh Kumar', 'principal@college.edu')
if c: Principal.objects.get_or_create(user=u)

# Vice Principal
u, c = create_if_not_exists('VP001', 'vp', 'Dr. Meena Sharma', 'vp@college.edu')
if c: VicePrincipal.objects.get_or_create(user=u)

# Manager
u, c = create_if_not_exists('MGR001', 'manager', 'Suresh Patil', 'manager@college.edu')
if c: Manager.objects.get_or_create(user=u)

# Accountant
u, c = create_if_not_exists('ACC001', 'accountant', 'Priya Nair', 'accountant@college.edu')
if c: Accountant.objects.get_or_create(user=u)

# Teachers
for i, (name, email) in enumerate([
    ('Prof. Amit Shah', 'amit@college.edu'),
    ('Prof. Kavita Rao', 'kavita@college.edu'),
    ('Prof. Rajan Verma', 'rajan@college.edu'),
], 1):
    login_id = f'STAFF{i:03d}'
    u, c = create_if_not_exists(login_id, 'teacher', name, email)
    if c: Teacher.objects.get_or_create(user=u, defaults={'qualification': 'M.Tech'})

print("\n✅ Seeding complete!")
print("\n📋 Login credentials:")
print("  PRINCIPAL01 / Welcome@123  →  Principal")
print("  VP001       / Welcome@123  →  Vice Principal")
print("  MGR001      / Welcome@123  →  Manager")
print("  ACC001      / Welcome@123  →  Accountant")
print("  STAFF001    / Welcome@123  →  Teacher")
print("\n🌐 Run server: python manage.py runserver")
print("📍 Visit: http://127.0.0.1:8000/login/\n")
