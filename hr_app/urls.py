from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # تسجيل الدخول والخروج
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard عام لتوجيه المستخدم حسب نوعه
    path('dashboard/', views.dashboard, name='dashboard'),

    # Dashboards حسب نوع المستخدم
    path('dashboard/employee/', views.dashboard_employee, name='dashboard_employee'),
    path('dashboard/hr/', views.dashboard_hr, name='dashboard_hr'),
    path('dashboard/finance/', views.dashboard_finance, name='dashboard_finance'),

    # Profile
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/', views.profile_view, name='profile'),
    path('contact-hr/', views.contact_hr, name='contact_hr'),
    path('hr/inbox/', views.hr_inbox, name='hr_inbox'),
    path('hr/message/<int:msg_id>/', views.view_message, name='view_message'),
    path('hr/message/<int:msg_id>/reply/', views.reply_message, name='reply_message'),

    # Employee inbox and message thread
    path('inbox/', views.employee_inbox, name='employee_inbox'),
    path('inbox/message/<int:msg_id>/', views.employee_view_message, name='employee_view_message'),
    path('inbox/message/<int:msg_id>/reply/', views.employee_reply_message, name='employee_reply_message'),

    # Attendance
    path('attendance/', views.attendance, name='attendance'),
    path('manage-attendance/', views.manage_attendance, name='manage_attendance'),

    # Leave
    path('request-leave/', views.request_leave, name='request_leave'),

    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    
    # HR / Admin management
    path('manage-employees/', views.manage_employees, name='manage_employees'),
    path('employees/add/', views.add_employee, name='add_employee'),
    path('employees/edit/<int:emp_id>/', views.edit_employee, name='edit_employee'),
    path('employees/delete/<int:emp_id>/', views.delete_employee, name='delete_employee'),

    # Leave management
    path('manage-leaves/', views.manage_leaves, name='manage_leaves'),
    path('leaves/approve/<int:leave_id>/', views.approve_leave, name='approve_leave'),
    path('leaves/reject/<int:leave_id>/', views.reject_leave, name='reject_leave'),

    # Payroll / Evaluations
    path('manage-payroll/', views.manage_payroll, name='manage_payroll'),
    path('payroll/edit/<int:pay_id>/', views.edit_payroll, name='edit_payroll'),
    path('manage-evaluations/', views.manage_evaluations, name='manage_evaluations'),
    path('payroll/export/', views.export_payroll, name='export_payroll'),
    path('payroll/add/', views.add_payroll, name='add_payroll'),
    path('payroll/export-pdf/', views.export_payroll_pdf, name='export_payroll_pdf'),
    path('employees/evaluate/add/', views.add_evaluation, name='add_evaluation'),
    path('employees/<int:emp_id>/details/', views.employee_details, name='employee_details'),


]
