from django.db import models
from django.utils import timezone


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
    ]

    student = models.ForeignKey(
        'accounts.Student', on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    timetable_slot = models.ForeignKey(
        'academics.Timetable', on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'timetable_slot', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.user.full_name} | {self.timetable_slot.subject.name} | {self.date} | {self.status}"
