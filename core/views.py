from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from accounts.models import Student, User
from academics.models import Semester
import json
import secrets
import string


@login_required
def api_manager_students(request):
    if request.user.role.name != 'manager':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.method == 'GET':
        sem_id = request.GET.get('semester_id', '')
        roll = request.GET.get('roll', '')
        students = Student.objects.select_related('user', 'semester')
        if sem_id:
            students = students.filter(semester_id=sem_id)
        if roll:
            students = students.filter(roll_number__icontains=roll)

        return JsonResponse({
            'students': [
                {
                    'id': s.id,
                    'full_name': s.full_name,
                    'roll_number': s.roll_number,
                    'email': s.email,
                    'phone': s.phone,
                    'semester': s.semester.number if s.semester else None,
                    'semester_id': s.semester.id if s.semester else None,
                    'is_active': s.is_active,
                    'enrollment_date': s.enrollment_date.isoformat() if s.enrollment_date else None,
                }
                for s in students
            ]
        })

    if request.method == 'POST':
        data = json.loads(request.body)
        full_name = data.get('full_name', '').strip()
        roll_number = data.get('roll_number', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        enrollment_date = data.get('enrollment_date') or None

        if not full_name or not roll_number:
            return JsonResponse({'error': 'Full name and roll number are required'}, status=400)

        if Student.objects.filter(roll_number=roll_number).exists():
            return JsonResponse({'error': f'Roll number {roll_number} already exists'}, status=400)

        # Get semester
        sem_id = data.get('semester_id')
        sem_num = data.get('semester_number')
        semester = None
        if sem_id:
            semester = Semester.objects.filter(id=sem_id).first()
        elif sem_num:
            semester = Semester.objects.filter(number=int(sem_num)).first()

        # Generate login ID from roll number
        login_id = roll_number.upper()
        if User.objects.filter(login_id=login_id).exists():
            login_id = f"{roll_number.upper()}_{secrets.token_hex(2)}"

        temp_password = ''.join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(8)
        )

        user = User.objects.create_user(login_id=login_id, password=temp_password, role_name='student')

        student = Student.objects.create(
            user=user,
            full_name=full_name,
            roll_number=roll_number,
            email=email,
            phone=phone,
            semester=semester,
            enrollment_date=enrollment_date,
        )

        return JsonResponse({
            'success': True,
            'login_id': login_id,
            'temp_password': temp_password,
            'student_id': student.id,
        })


@login_required
def api_manager_student_detail(request, student_id):
    if request.user.role.name != 'manager':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    student = get_object_or_404(Student, id=student_id)

    # Get attendance summary
    from attendance.models import Attendance
    from academics.models import Subject
    att_records = Attendance.objects.filter(student=student)
    total = att_records.count()
    present = att_records.filter(status='present').count()
    att_pct = round(present / total * 100, 1) if total > 0 else 0

    # Get fee status
    from fees.models import StudentFee
    latest_fee = StudentFee.objects.filter(student=student).order_by('-created_at').first()
    fee_status = latest_fee.status if latest_fee else 'no record'

    return JsonResponse({
        'student': {
            'id': student.id,
            'full_name': student.full_name,
            'roll_number': student.roll_number,
            'email': student.email,
            'phone': student.phone,
            'semester': student.semester.number if student.semester else None,
            'is_active': student.is_active,
            'enrollment_date': student.enrollment_date.isoformat() if student.enrollment_date else None,
            'attendance_pct': att_pct,
            'fee_status': fee_status,
        }
    })
