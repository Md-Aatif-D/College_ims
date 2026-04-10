from django.urls import path
from . import views

urlpatterns = [
    path('api/fees/semester/', views.api_semester_fees, name='api_semester_fees'),
    path('api/fees/student/', views.api_student_fees, name='api_student_fees'),
    path('api/fees/dashboard/', views.api_fee_dashboard, name='api_fee_dashboard'),
]
