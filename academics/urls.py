from django.urls import path
from . import views

urlpatterns = [
    path('api/semesters/', views.api_semesters, name='api_semesters'),
    path('api/semesters/<int:sem_id>/toggle/', views.api_semester_toggle, name='api_semester_toggle'),
    path('api/subjects/', views.api_subjects, name='api_subjects'),
    path('api/teacher-assignments/', views.api_teacher_assignments, name='api_teacher_assignments'),
    path('api/timetable/', views.api_timetable, name='api_timetable'),
]
