from django.db import models


class SemesterFee(models.Model):
    """VP sets fee for each semester"""
    semester = models.OneToOneField(
        'academics.Semester', on_delete=models.CASCADE,
        related_name='fee_structure'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    set_by = models.ForeignKey(
        'accounts.Accountant', on_delete=models.SET_NULL,
        null=True, related_name='fee_structures'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Sem {self.semester.number} Fee: ₹{self.amount}"


class StudentFee(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('partial', 'Partial'),
    ]

    student = models.ForeignKey(
        'accounts.Student', on_delete=models.CASCADE,
        related_name='fee_records'
    )
    semester = models.ForeignKey(
        'academics.Semester', on_delete=models.CASCADE,
        related_name='student_fees'
    )
    fee_structure = models.ForeignKey(
        SemesterFee, on_delete=models.CASCADE,
        related_name='student_payments'
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    entered_by = models.ForeignKey(
        'accounts.Accountant', on_delete=models.SET_NULL,
        null=True, related_name='entered_payments'
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'semester')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} | Sem {self.semester.number} | {self.status}"

    @property
    def pending_amount(self):
        return self.fee_structure.amount - self.amount_paid

    def save(self, *args, **kwargs):
        if self.amount_paid >= self.fee_structure.amount:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'
        super().save(*args, **kwargs)
