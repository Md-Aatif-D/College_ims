from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import SemesterFee, StudentFee
from academics.models import Semester
import json


@login_required
def api_semester_fees(request):
    if request.method == 'GET':
        sem_id = request.GET.get('semester_id')
        fees = SemesterFee.objects.select_related('semester')
        if sem_id:
            fees = fees.filter(semester_id=sem_id)
        return JsonResponse({
            'fees': [
                {
                    'id': f.id,
                    'semester': f.semester.number,
                    'amount': float(f.amount),
                    'due_date': f.due_date.isoformat() if f.due_date else None,
                }
                for f in fees
            ]
        })

    if request.user.role.name != 'accountant':
        return JsonResponse({'error': 'Only accountant can set fees'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        fee, created = SemesterFee.objects.update_or_create(
            semester_id=data['semester_id'],
            defaults={
                'amount': data['amount'],
                'due_date': data.get('due_date'),
                'set_by': request.user.accountant_profile,
            }
        )
        return JsonResponse({'success': True, 'id': fee.id, 'created': created})


@login_required
def api_student_fees(request):
    if request.method == 'GET':
        user = request.user

        if user.role.name == 'student':
            student = user.student_profile
            records = StudentFee.objects.filter(
                student=student
            ).select_related('semester', 'fee_structure')
            return JsonResponse({
                'fees': [
                    {
                        'semester': r.semester.number,
                        'total_fee': float(r.fee_structure.amount),
                        'amount_paid': float(r.amount_paid),
                        'pending': float(r.pending_amount),
                        'status': r.status,
                        'payment_date': r.payment_date.isoformat() if r.payment_date else None,
                        'due_date': r.fee_structure.due_date.isoformat() if r.fee_structure.due_date else None,
                    }
                    for r in records
                ]
            })

        if user.role.name == 'accountant':
            student_id = request.GET.get('student_id')
            semester_id = request.GET.get('semester_id')
            status_filter = request.GET.get('status')

            records = StudentFee.objects.select_related(
                'student', 'semester', 'fee_structure'
            )
            if student_id:
                records = records.filter(student_id=student_id)
            if semester_id:
                records = records.filter(semester_id=semester_id)
            if status_filter:
                records = records.filter(status=status_filter)

            from django.db.models import Sum
            dashboard_stats = StudentFee.objects.aggregate(
                total_collected=Sum('amount_paid'),
                total_pending=Sum('fee_structure__amount')
            )

            return JsonResponse({
                'fees': [
                    {
                        'id': r.id,
                        'student_name': r.student.full_name,
                        'roll_number': r.student.roll_number,
                        'semester': r.semester.number,
                        'total_fee': float(r.fee_structure.amount),
                        'amount_paid': float(r.amount_paid),
                        'pending': float(r.pending_amount),
                        'status': r.status,
                        'payment_date': r.payment_date.isoformat() if r.payment_date else None,
                    }
                    for r in records
                ]
            })

        return JsonResponse({'error': 'Forbidden'}, status=403)

    if request.user.role.name != 'accountant':
        return JsonResponse({'error': 'Only accountant can enter payments'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        student_id = data['student_id']
        semester_id = data['semester_id']

        fee_structure = get_object_or_404(SemesterFee, semester_id=semester_id)
        student_fee, created = StudentFee.objects.get_or_create(
            student_id=student_id,
            semester_id=semester_id,
            defaults={
                'fee_structure': fee_structure,
                'entered_by': request.user.accountant_profile,
            }
        )
        student_fee.amount_paid = data['amount_paid']
        student_fee.payment_date = data.get('payment_date')
        student_fee.transaction_id = data.get('transaction_id', '')
        student_fee.remarks = data.get('remarks', '')
        student_fee.entered_by = request.user.accountant_profile
        student_fee.save()

        return JsonResponse({
            'success': True,
            'status': student_fee.status,
            'pending': float(student_fee.pending_amount),
        })


@login_required
def api_fee_dashboard(request):
    """Accountant dashboard stats"""
    if request.user.role.name != 'accountant':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    from django.db.models import Sum, Count
    stats = {
        'total_collected': float(
            StudentFee.objects.filter(status='paid').aggregate(
                t=Sum('amount_paid'))['t'] or 0
        ),
        'total_pending_amount': float(
            StudentFee.objects.filter(
                status__in=['pending', 'partial']
            ).aggregate(
                t=Sum('fee_structure__amount'))['t'] or 0
        ),
        'paid_count': StudentFee.objects.filter(status='paid').count(),
        'pending_count': StudentFee.objects.filter(status='pending').count(),
        'partial_count': StudentFee.objects.filter(status='partial').count(),
    }
    return JsonResponse(stats)
