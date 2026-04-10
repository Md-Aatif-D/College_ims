from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('change-password/', views.change_password_view, name='change_password'),

    # API endpoints
    path('api/profile/', views.api_profile, name='api_profile'),
    path('api/dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),

    # User management (Principal)
    path('api/users/', views.api_manage_users, name='api_manage_users'),
    path('api/users/<int:user_id>/toggle/', views.api_toggle_user, name='api_toggle_user'),

    # Password reset
    path('api/password-reset/request/', views.api_request_password_reset, name='api_request_reset'),
    path('api/password-reset/manage/', views.api_reset_requests, name='api_reset_requests'),
]
