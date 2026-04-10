from django.urls import path
from . import views

urlpatterns = [
    path('api/attendance/mark/', views.api_mark_attendance, name='api_mark_attendance'),
    path('api/attendance/report/', views.api_attendance_report, name='api_attendance_report'),
]
