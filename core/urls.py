from django.urls import path
from . import views

urlpatterns = [
    path('api/manager/students/', views.api_manager_students, name='api_manager_students'),
    path('api/manager/students/<int:student_id>/', views.api_manager_student_detail, name='api_manager_student_detail'),
]
