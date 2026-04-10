from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
import json
import secrets
import string


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/home.html')

def get_user_full_name(user):
    """Get display name for any role"""
    return user.full_name



def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        login_id = data.get('login_id', '')
        password = data.get('password', '')
        user = authenticate(request, username=login_id, password=password)
        if user and user.is_active:
            login(request, user)
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'role': user.role,
                    'must_change_password': user.must_change_password,
                    'redirect': '/dashboard/'
                })
            if user.must_change_password:
                return redirect('change_password')
            return redirect('dashboard')
        if request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)
        return render(request, 'accounts/login.html', {'error': 'Invalid Login ID or Password'})
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    user = request.user
    context = {
        'user': user,
        'full_name': user.full_name,
        'role': user.role,
    }
    return render(request, f'dashboards/{user.role.name}_dashboard.html', context)


@login_required
def change_password_view(request):
    if request.method == 'POST':
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        if new_password != confirm_password:
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': 'Passwords do not match'})
            return render(request, 'accounts/change_password.html', {'error': 'Passwords do not match'})
        if len(new_password) < 8:
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters'})
            return render(request, 'accounts/change_password.html', {'error': 'Password must be at least 8 characters'})
        request.user.set_password(new_password)
        request.user.must_change_password = False
        request.user.save()
        login(request, request.user)
        if request.content_type == 'application/json':
            return JsonResponse({'success': True, 'redirect': '/dashboard/'})
        return redirect('dashboard')
    return render(request, 'accounts/change_password.html')


# ─── API Views ──────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """Stats for all dashboards"""
    from accounts.models import Teacher, Student
    from academics.models import Semester, Subject
    from accounts.models import PasswordResetRequest
    from fees.models import StudentFee

    user = request.user
    data = {'role': user.role, 'full_name': user.full_name}

    if user.role.name == 'principal':
        data.update({
            'total_students': Student.objects.filter(is_active=True).count(),
            'total_teachers': Teacher.objects.count(),
            'active_semesters': Semester.objects.filter(is_current=True).count(),
            'pending_resets': PasswordResetRequest.objects.filter(status='pending').count(),
        })
    elif user.role.name == 'vp':
        current_sem = Semester.objects.filter(is_current=True).first()
        data.update({
            'current_semester': current_sem.number if current_sem else None,
            'total_subjects': Subject.objects.filter(is_active=True).count(),
            'total_teachers': Teacher.objects.count(),
            'total_students': Student.objects.filter(is_active=True).count(),
        })
    elif user.role.name == 'manager':
        data.update({
            'total_students': Student.objects.filter(is_active=True).count(),
            'inactive_students': Student.objects.filter(is_active=False).count(),
            'pending_resets': PasswordResetRequest.objects.filter(
                status='pending', user__role__name='student'
            ).count(),
        })
    elif user.role.name == 'accountant':
        from django.db.models import Sum
        total_collected = StudentFee.objects.filter(status='paid').aggregate(
            total=Sum('amount_paid'))['total'] or 0
        total_pending = StudentFee.objects.filter(status__in=['pending', 'partial']).count()
        data.update({
            'total_collected': float(total_collected),
            'total_pending_cases': total_pending,
        })
    elif user.role.name == 'teacher':
        from academics.models import TeacherAssignment
        assignments = TeacherAssignment.objects.filter(
            teacher=user.teacher_profile
        ).select_related('subject', 'semester')
        data.update({
            'assignments': [
                {
                    'subject': a.subject.name,
                    'subject_code': a.subject.code,
                    'semester': a.semester.number
                } for a in assignments
            ]
        })
    elif user.role.name == 'student':
        student = user.student_profile
        pending_fees = StudentFee.objects.filter(
            student=student, status__in=['pending', 'partial']
        ).count()
        data.update({
            'roll_number': student.roll_number,
            'semester': student.semester.number if student.semester else None,
            'pending_fees': pending_fees,
        })
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def api_profile(request):
    user = request.user
    return JsonResponse({
        'login_id': user.login_id,
        'role': user.role,
        'full_name': user.full_name,
        'must_change_password': user.must_change_password,
    })


# ─── Principal: Manage Roles ─────────────────────────────────────────────────

@login_required
def api_manage_users(request):
    if request.user.role.name not in ['principal']:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    from accounts.models import (VicePrincipal, Manager, Accountant, Teacher,
                                  Student, User)

    if request.method == 'GET':
        role = request.GET.get('role', '')
        users = User.objects.filter(role__name=role) if role else User.objects.all()
        result = []
        for u in users:
            entry = {
                'id': u.id, 'login_id': u.login_id,
                'role': u.role, 'is_active': u.is_active,
                'full_name': get_user_full_name(u)
            }
            result.append(entry)
        return JsonResponse({'users': result})

    if request.method == 'POST':
        data = json.loads(request.body)
        role = data.get('role')
        login_id = data.get('login_id')
        full_name = data.get('full_name')
        email = data.get('email', '')

        if User.objects.filter(login_id=login_id).exists():
            return JsonResponse({'error': 'Login ID already exists'}, status=400)

        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        user = User.objects.create_user(login_id=login_id, password=temp_password, role_name=role)

        profile_map = {
            'vp': VicePrincipal,
            'manager': Manager,
            'accountant': Accountant,
            'teacher': Teacher,
        }
        if role in profile_map:
            profile_map[role].objects.create(user=user, full_name=full_name, email=email)

        return JsonResponse({
            'success': True,
            'login_id': login_id,
            'temp_password': temp_password,
            'message': f'User {login_id} created. Temp password: {temp_password}'
        })


@login_required
def api_toggle_user(request, user_id):
    if request.user.role.name not in ['principal']:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    from accounts.models import User
    target = get_object_or_404(User, id=user_id)
    target.is_active = not target.is_active
    target.save()
    return JsonResponse({'success': True, 'is_active': target.is_active})


# ─── Password Reset ───────────────────────────────────────────────────────────

@csrf_exempt
def api_request_password_reset(request):
    if request.method == 'POST':
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        login_id = data.get('login_id')
        from accounts.models import PasswordResetRequest, User
        
        user = User.objects.filter(login_id=login_id).first()
        if not user:
            # Fake success to prevent user enumeration
            return JsonResponse({'success': True, 'message': 'If the user exists, a request has been submitted.'})
            
        existing = PasswordResetRequest.objects.filter(
            user=user, status='pending'
        )
        if existing.exists():
            return JsonResponse({'error': 'Reset request already pending'}, status=400)
            
        PasswordResetRequest.objects.create(user=user)
        return JsonResponse({'success': True, 'message': 'Reset request submitted'})


@login_required
def api_reset_requests(request):
    """For approvers (principal/vp/manager) to view & approve"""
    from accounts.models import PasswordResetRequest, User
    user = request.user
    approver_role_map = {
        'principal': ['vp', 'manager', 'accountant', 'teacher'],
        'vp': ['teacher'],
        'manager': ['student'],
    }
    allowed_roles = approver_role_map.get(user.role, [])

    if request.method == 'GET':
        requests = PasswordResetRequest.objects.filter(
            status='pending', user__role__in=allowed_roles
        ).select_related('user')
        return JsonResponse({
            'requests': [
                {
                    'id': r.id,
                    'login_id': r.user.login_id,
                    'role': r.user.role,
                    'full_name': get_user_full_name(r.user),
                    'requested_at': r.requested_at.isoformat(),
                }
                for r in requests
            ]
        })

    if request.method == 'POST':
        data = json.loads(request.body)
        req_id = data.get('request_id')
        action = data.get('action')  # 'approve' or 'reject'
        reset_req = get_object_or_404(PasswordResetRequest, id=req_id)

        if reset_req.user.role not in allowed_roles:
            return JsonResponse({'error': 'Not authorized to approve this'}, status=403)

        if action == 'approve':
            temp_password = ''.join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(8)
            )
            reset_req.user.set_password(temp_password)
            reset_req.user.must_change_password = True
            reset_req.user.save()
            reset_req.status = 'approved'
            reset_req.approved_by = user
            reset_req.temp_password = temp_password
            reset_req.resolved_at = timezone.now()
            reset_req.save()
            return JsonResponse({
                'success': True,
                'temp_password': temp_password,
                'message': f'Password reset to: {temp_password}'
            })
        else:
            reset_req.status = 'rejected'
            reset_req.approved_by = user
            reset_req.resolved_at = timezone.now()
            reset_req.save()
            return JsonResponse({'success': True, 'message': 'Request rejected'})
