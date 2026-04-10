from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Attendance
from academics.models import Timetable, Subject, Semester
import json
from datetime import date


@login_required
def api_mark_attendance(request):
    if request.user.role.name != 'teacher':
        return JsonResponse({'error': 'Only teachers can mark attendance'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        teacher = request.user.teacher_profile
        subject_id = data.get('subject_id')
        semester_id = data.get('semester_id')
        attendance_date = data.get('date', date.today().isoformat())
        records = data.get('records', [])  # [{'student_id': x, 'status': 'present'|'absent'}]

        # Validate: teacher must be assigned to this subject
        from academics.models import TeacherAssignment
        is_assigned = TeacherAssignment.objects.filter(
            teacher=teacher, subject_id=subject_id, semester_id=semester_id
        ).exists()
        if not is_assigned:
            return JsonResponse({'error': 'You are not assigned to this subject'}, status=403)

        # Time restriction: must be during class time
        # (simplified - check timetable for today's day)
        today_name = date.today().strftime('%A').lower()
        slot = Timetable.objects.filter(
            subject_id=subject_id, semester_id=semester_id, day=today_name
        ).first()

        created_count = 0
        updated_count = 0
        for record in records:
            obj, created = Attendance.objects.update_or_create(
                student_id=record['student_id'],
                subject_id=subject_id,
                date=attendance_date,
                defaults={
                    'semester_id': semester_id,
                    'teacher': teacher,
                    'status': record['status'],
                    'timetable_slot': slot,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        return JsonResponse({
            'success': True,
            'created': created_count,
            'updated': updated_count,
            'message': f'Attendance marked: {created_count} new, {updated_count} updated'
        })

    if request.method == 'GET':
        """Get students list for marking attendance"""
        from accounts.models import Student
        subject_id = request.GET.get('subject_id')
        semester_id = request.GET.get('semester_id')
        attendance_date = request.GET.get('date', date.today().isoformat())

        students = Student.objects.filter(
            semester_id=semester_id, is_active=True
        ).select_related('user')

        # Get existing attendance for today
        existing = {
            a.student_id: a.status
            for a in Attendance.objects.filter(
                subject_id=subject_id, date=attendance_date
            )
        }

        return JsonResponse({
            'students': [
                {
                    'id': s.id,
                    'full_name': s.full_name,
                    'roll_number': s.roll_number,
                    'status': existing.get(s.id, 'unmarked'),
                }
                for s in students
            ],
            'date': attendance_date,
        })


@login_required
def api_attendance_report(request):
    """Get attendance summary for student or teacher"""
    user = request.user

    if user.role.name == 'student':
        student = user.student_profile
        sem_id = request.GET.get('semester_id') or (
            student.semester.id if student.semester else None
        )
        subject_id = request.GET.get('subject_id')

        records = Attendance.objects.filter(
            student=student, semester_id=sem_id
        )
        if subject_id:
            records = records.filter(subject_id=subject_id)

        subjects = Subject.objects.filter(
            semester_id=sem_id, is_active=True
        )
        summary = []
        for subj in subjects:
            subj_records = records.filter(subject=subj)
            total = subj_records.count()
            present = subj_records.filter(status='present').count()
            summary.append({
                'subject_id': subj.id,
                'subject_name': subj.name,
                'subject_code': subj.code,
                'total_classes': total,
                'present': present,
                'absent': total - present,
                'percentage': round((present / total * 100), 1) if total > 0 else 0,
            })
        return JsonResponse({'summary': summary})

    elif user.role.name == 'teacher':
        teacher = user.teacher_profile
        subject_id = request.GET.get('subject_id')
        semester_id = request.GET.get('semester_id')
        attendance_date = request.GET.get('date')

        records = Attendance.objects.filter(teacher=teacher)
        if subject_id:
            records = records.filter(subject_id=subject_id)
        if semester_id:
            records = records.filter(semester_id=semester_id)
        if attendance_date:
            records = records.filter(date=attendance_date)

        return JsonResponse({
            'records': [
                {
                    'student_name': r.student.full_name,
                    'roll_number': r.student.roll_number,
                    'subject': r.subject.name,
                    'date': r.date.isoformat(),
                    'status': r.status,
                }
                for r in records.select_related('student', 'subject')[:100]
            ]
        })

    elif user.role.name in ['vp', 'principal', 'manager']:
        # Admin view of attendance
        subject_id = request.GET.get('subject_id')
        semester_id = request.GET.get('semester_id')
        student_id = request.GET.get('student_id')

        records = Attendance.objects.all()
        if subject_id:
            records = records.filter(subject_id=subject_id)
        if semester_id:
            records = records.filter(semester_id=semester_id)
        if student_id:
            records = records.filter(student_id=student_id)

        return JsonResponse({
            'records': [
                {
                    'student_name': r.student.full_name,
                    'roll_number': r.student.roll_number,
                    'subject': r.subject.name,
                    'date': r.date.isoformat(),
                    'status': r.status,
                }
                for r in records.select_related('student', 'subject')[:200]
            ]
        })

    return JsonResponse({'error': 'Unauthorized'}, status=403)
