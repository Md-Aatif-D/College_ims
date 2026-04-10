from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from .models import Semester, Subject, TeacherAssignment, Timetable
import json


def role_required(*roles):
    def decorator(func):
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                return JsonResponse({'error': 'Forbidden'}, status=403)
            return func(request, *args, **kwargs)
        return wrapped
    return decorator


# ─── Semester APIs ────────────────────────────────────────────────────────────

@login_required
def api_semesters(request):
    if request.method == 'GET':
        sems = Semester.objects.all()
        return JsonResponse({
            'semesters': [
                {
                    'id': s.id, 'number': s.number,
                    'is_current': s.is_current,
                    'start_date': s.start_date.isoformat() if s.start_date else None,
                    'end_date': s.end_date.isoformat() if s.end_date else None,
                }
                for s in sems
            ]
        })

    if request.user.role.name != 'vp':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        number = data.get('number')
        if Semester.objects.filter(number=number).exists():
            return JsonResponse({'error': f'Semester {number} already exists'}, status=400)
        sem = Semester.objects.create(
            number=number,
            is_current=data.get('is_current', False),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
        )
        return JsonResponse({'success': True, 'id': sem.id, 'number': sem.number})


@login_required
def api_semester_toggle(request, sem_id):
    if request.user.role.name != 'vp':
        return JsonResponse({'error': 'Forbidden'}, status=403)
    sem = get_object_or_404(Semester, id=sem_id)
    sem.is_current = not sem.is_current
    sem.save()
    return JsonResponse({'success': True, 'is_current': sem.is_current})


# ─── Subject APIs ─────────────────────────────────────────────────────────────

@login_required
def api_subjects(request):
    if request.method == 'GET':
        sem_id = request.GET.get('semester_id')
        subjects = Subject.objects.select_related('semester')
        if sem_id:
            subjects = subjects.filter(semester_id=sem_id)
        if request.user.role.name == 'teacher':
            # Teachers see only their assigned subjects
            teacher = request.user.teacher_profile
            assigned_ids = TeacherAssignment.objects.filter(
                teacher=teacher
            ).values_list('subject_id', flat=True)
            subjects = subjects.filter(id__in=assigned_ids)
        elif request.user.role.name == 'student':
            # Students see subjects in their semester
            student = request.user.student_profile
            if student.semester:
                subjects = subjects.filter(semester=student.semester)

        return JsonResponse({
            'subjects': [
                {
                    'id': s.id, 'name': s.name, 'code': s.code,
                    'semester': s.semester.number, 'credits': s.credits,
                    'is_active': s.is_active,
                }
                for s in subjects
            ]
        })

    if request.user.role.name != 'vp':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        subject = Subject.objects.create(
            name=data['name'],
            code=data['code'],
            semester_id=data['semester_id'],
            credits=data.get('credits', 3),
            description=data.get('description', ''),
        )
        return JsonResponse({'success': True, 'id': subject.id})

    if request.method == 'DELETE':
        data = json.loads(request.body)
        Subject.objects.filter(id=data.get('id')).update(is_active=False)
        return JsonResponse({'success': True})


# ─── Teacher Assignment APIs ──────────────────────────────────────────────────

@login_required
def api_teacher_assignments(request):
    if request.method == 'GET':
        sem_id = request.GET.get('semester_id')
        assignments = TeacherAssignment.objects.select_related(
            'teacher', 'subject', 'semester'
        )
        if sem_id:
            assignments = assignments.filter(semester_id=sem_id)
        if request.user.role.name == 'teacher':
            assignments = assignments.filter(teacher=request.user.teacher_profile)

        return JsonResponse({
            'assignments': [
                {
                    'id': a.id,
                    'teacher_id': a.teacher.id,
                    'teacher_name': a.teacher.full_name,
                    'subject_id': a.subject.id,
                    'subject_name': a.subject.name,
                    'subject_code': a.subject.code,
                    'semester': a.semester.number,
                }
                for a in assignments
            ]
        })

    if request.user.role.name != 'vp':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        # Check: one teacher → one subject per semester
        existing = TeacherAssignment.objects.filter(
            teacher_id=data['teacher_id'],
            semester_id=data['semester_id']
        ).first()
        if existing:
            return JsonResponse({
                'error': f'Teacher already assigned to {existing.subject.name} in this semester'
            }, status=400)

        assignment = TeacherAssignment.objects.create(
            teacher_id=data['teacher_id'],
            subject_id=data['subject_id'],
            semester_id=data['semester_id'],
        )
        return JsonResponse({'success': True, 'id': assignment.id})


# ─── Timetable APIs ───────────────────────────────────────────────────────────

@login_required
def api_timetable(request):
    if request.method == 'GET':
        sem_id = request.GET.get('semester_id')

        if request.user.role.name == 'student':
            student = request.user.student_profile
            sem_id = student.semester.id if student.semester else None
        elif request.user.role.name == 'teacher':
            teacher = request.user.teacher_profile
            slots = Timetable.objects.filter(
                teacher=teacher
            ).select_related('subject', 'semester')
            return JsonResponse({
                'timetable': [
                    {
                        'id': t.id, 'day': t.day,
                        'start_time': t.start_time.strftime('%H:%M'),
                        'end_time': t.end_time.strftime('%H:%M'),
                        'subject': t.subject.name,
                        'semester': t.semester.number,
                    }
                    for t in slots
                ]
            })

        timetable = Timetable.objects.select_related('subject', 'teacher', 'semester')
        if sem_id:
            timetable = timetable.filter(semester_id=sem_id)

        return JsonResponse({
            'timetable': [
                {
                    'id': t.id, 'day': t.day,
                    'start_time': t.start_time.strftime('%H:%M'),
                    'end_time': t.end_time.strftime('%H:%M'),
                    'subject': t.subject.name,
                    'subject_code': t.subject.code,
                    'teacher': t.teacher.full_name if t.teacher else 'Unassigned',
                    'semester': t.semester.number,
                }
                for t in timetable
            ]
        })

    if request.user.role.name != 'vp':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        # Check for clash: same semester + day + time
        clash = Timetable.objects.filter(
            semester_id=data['semester_id'],
            day=data['day'],
            start_time=data['start_time'],
        ).first()
        if clash:
            return JsonResponse({'error': 'Time slot clash! Another class is scheduled at this time.'}, status=400)

        slot = Timetable.objects.create(
            semester_id=data['semester_id'],
            subject_id=data['subject_id'],
            teacher_id=data.get('teacher_id'),
            day=data['day'],
            start_time=data['start_time'],
            end_time=data['end_time'],
        )
        return JsonResponse({'success': True, 'id': slot.id})

    if request.method == 'DELETE':
        data = json.loads(request.body)
        Timetable.objects.filter(id=data['id']).delete()
        return JsonResponse({'success': True})
