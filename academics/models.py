from django.db import models
from django.utils import timezone


class Semester(models.Model):
    COURSE_CHOICES = [
        ('BCA', 'BCA'),
        ('MSC', 'MSC'),
    ]
    number = models.IntegerField()  # removed unique=True since multiple courses can have Semester 1
    course = models.CharField(max_length=10, choices=COURSE_CHOICES, default='BCA')
    is_current = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('number', 'course')
        ordering = ['course', 'number']

    def __str__(self):
        return f"{self.course} - Semester {self.number}"

    def save(self, *args, **kwargs):
        # Enforce only one active semester
        if self.is_current:
            Semester.objects.filter(is_current=True, course=self.course).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Subject(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    credits = models.IntegerField(default=3)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name} (Sem {self.semester.number})"

    class Meta:
        ordering = ['semester', 'name']


class TeacherAssignment(models.Model):
    """One teacher → one subject per semester"""
    teacher = models.ForeignKey(
        'accounts.Teacher', on_delete=models.CASCADE,
        related_name='assignments'
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE,
        related_name='assignments'
    )
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE,
        related_name='teacher_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('teacher', 'subject', 'semester')

    def __str__(self):
        return f"{self.teacher.full_name} → {self.subject.name} (Sem {self.semester.number})"


class Timetable(models.Model):
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]

    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='timetable')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetable')
    teacher = models.ForeignKey(
        'accounts.Teacher', on_delete=models.CASCADE,
        related_name='timetable', null=True, blank=True
    )
    day = models.CharField(max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day', 'start_time']
        # No double-booking: one slot per semester-day-time
        unique_together = ('semester', 'day', 'start_time')

    def __str__(self):
        return f"Sem{self.semester.number} | {self.day} {self.start_time}-{self.end_time} | {self.subject.name}"
