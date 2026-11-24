from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_student, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('apply/<int:scholarship_id>/', views.apply_scholarship, name='apply_scholarship'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/update/<int:app_id>/', views.update_application_status, name='update_status'),
    path('admin-panel/export-csv/', views.export_report_csv, name='export_report_csv'),
]
