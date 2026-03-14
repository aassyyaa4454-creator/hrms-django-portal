# hr_app/views.py

# --- 1. Python Standard Library ---
import asyncio
import csv
import os
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from io import BytesIO

# --- 2. Django Core Libraries ---
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.db.models import Avg
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template, render_to_string
from django.utils import timezone

# --- 3. Third-Party Libraries ---
from playwright.async_api import async_playwright
# إذا كنت لا تزال تستخدم xhtml2pdf، يمكنك إبقاء هذه الاستدعاءات
from xhtml2pdf import pisa
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 4. Local Application Imports ---
from .models import (
    Attendance,
    Evaluation,
    LeaveRequest,
    Message,
    Notification,
    Payroll,
    Profile,
)



# ----------------------------
# Helpers
# ----------------------------

def to_decimal(val, default=Decimal('0.00')):
    """
    تقوم بتحويل القيمة إلى Decimal بشكل آمن، وتعيد قيمة افتراضية عند الفشل.
    """
    try:
        if val in (None, ''):
            return default
        return Decimal(val)
    except (InvalidOperation, TypeError):
        return default

def is_hr_manager(user):
    return Profile.objects.filter(user=user, user_type='HR Manager').exists() or user.is_superuser


# ----------------------------
# Helpers
# ----------------------------
def is_hr_manager(user):
    return Profile.objects.filter(user=user, user_type='HR Manager').exists() or user.is_superuser

def is_employee(user):
    return Profile.objects.filter(user=user, user_type='Employee').exists()

def is_finance(user):
    return Profile.objects.filter(user=user, user_type='Finance').exists()

# ----------------------------
# General Pages
# ----------------------------
def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'})
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

# ----------------------------
# General Dashboard Router
# ----------------------------
@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('/admin/')
    elif is_hr_manager(request.user):
        return redirect('dashboard_hr')
    elif is_employee(request.user):
        return redirect('dashboard_employee')
    elif is_finance(request.user):
        return redirect('dashboard_finance')
    else:
        return redirect('home')

# ----------------------------
# Dashboards
# ----------------------------
# hr_app/views.py

@login_required
@user_passes_test(is_hr_manager)
def dashboard_hr(request):
    # جلب الإحصائيات الأساسية مع استثناء الـ superuser
    total_employees = Profile.objects.filter(user__is_superuser=False, user_type='Employee').count()
    pending_leaves = LeaveRequest.objects.filter(status='Pending').count()
    today_attendance = Attendance.objects.filter(date=timezone.now().date()).count()
    
    # --- حساب متوسط التقييمات ---
    # 1. نقوم بحساب المتوسط باستخدام Avg من قاعدة البيانات مباشرة
    avg_eval_dict = Evaluation.objects.aggregate(average_score=Avg('score'))
    
    # 2. نقوم بتنسيق النتيجة
    average_performance = avg_eval_dict.get('average_score')
    if average_performance is not None:
        # نقرب النتيجة لرقمين عشريين
        average_performance = round(average_performance, 2)
    else:
        # إذا لم تكن هناك تقييمات، نعرض 0
        average_performance = 0
        
    context = {
        'total_employees': total_employees,
        'pending_leaves': pending_leaves,
        'today_attendance': today_attendance,
        'average_performance': average_performance, # <-- نرسل القيمة المحسوبة
    }
    return render(request, 'dashboards/dashboard_admin.html', context)
@login_required
@user_passes_test(is_employee)
def dashboard_employee(request):
    profile = Profile.objects.get(user=request.user)
    payroll = Payroll.objects.filter(employee=profile).first()
    evaluations = Evaluation.objects.filter(employee=profile).order_by('-month')
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    context = {
        'employee': profile,
        'payroll': payroll,
        'performance': evaluations.first() if evaluations.exists() else None,
        'notifications': notifications,
    }
    return render(request, 'dashboards/dashboard_employee.html', context)

@login_required
@user_passes_test(is_finance)
def dashboard_finance(request):
    payrolls = Payroll.objects.all()
    context = {'payrolls': payrolls}
    return render(request, 'dashboards/dashboard_finance.html', context)

# ----------------------------
# Profile Update
# ----------------------------
@login_required
def update_profile(request):
    # Ensure a Profile exists for the user; create a default Employee profile if missing
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'user_type': 'Employee'}
    )
    if request.method == 'POST':
        profile.phone = request.POST.get('phone')
        profile.qualification = request.POST.get('qualification')
        profile.address = request.POST.get('address')
        if 'photo' in request.FILES:
            profile.photo = request.FILES['photo']
        profile.save()
        # توجيه حسب نوع المستخدم
        return redirect('dashboard')
    return render(request, 'update_profile.html', {'profile': profile})


@login_required
def profile_view(request):
    """Render the user's profile page and show payroll history for the employee."""
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'user_type': 'Employee'}
    )
    # Only show payrolls related to this profile
    payrolls = Payroll.objects.filter(employee=profile).order_by('-year', '-month')
    return render(request, 'profile.html', {'profile': profile, 'payrolls': payrolls})

# ----------------------------
# Attendance
# ----------------------------
@login_required
@user_passes_test(is_employee)
def attendance(request):
    # If profile missing create a default Employee profile to avoid 500 errors
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'user_type': 'Employee'}
    )
    today = timezone.now().date()
    attendance_record, created = Attendance.objects.get_or_create(employee=profile, date=today)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'check_in' and not attendance_record.check_in:
            attendance_record.check_in = timezone.now().time()
        elif action == 'check_out' and not attendance_record.check_out:
            attendance_record.check_out = timezone.now().time()
            if attendance_record.check_in:
                t_in = datetime.combine(today, attendance_record.check_in)
                t_out = datetime.combine(today, attendance_record.check_out)
                delta = t_out - t_in
                attendance_record.hours_worked = round(delta.total_seconds() / 3600, 2)
        attendance_record.save()
        return redirect('attendance')

    return render(request, 'attendance.html', {'attendance': attendance_record})

@login_required
@user_passes_test(is_hr_manager)
def manage_attendance(request):
    attendances = Attendance.objects.select_related('employee__user').order_by('-date')
    if request.method == 'POST':
        attendance_id = request.POST.get('attendance_id')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        attendance = Attendance.objects.get(id=attendance_id)
        if check_in:
            attendance.check_in = check_in
        if check_out:
            attendance.check_out = check_out
            if attendance.check_in:
                t_in = datetime.combine(attendance.date, attendance.check_in)
                t_out = datetime.combine(attendance.date, attendance.check_out)
                delta = t_out - t_in
                attendance.hours_worked = round(delta.total_seconds()/3600, 2)
        attendance.save()
        return redirect('manage_attendance')
    return render(request, 'manage_attendance.html', {'attendances': attendances})

# ----------------------------
# Leave Request
# ----------------------------
@login_required
@user_passes_test(is_employee)
def request_leave(request):
    # Ensure Profile exists; if not, create a default Employee profile
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'user_type': 'Employee'}
    )
    if request.method == 'POST':
        leave_type = request.POST.get('leave_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')
        LeaveRequest.objects.create(
            employee=profile,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        return redirect('request_leave')
    return render(request, 'request_leave.html')

# ----------------------------
# Notifications
# ----------------------------
@login_required
def notifications(request):
    notes = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notes})


# ----------------------------
# Messaging: Employee -> HR and HR replies
# ----------------------------
# hr_app/views.py

@login_required
@user_passes_test(is_employee)
def contact_hr(request):
    if request.method == 'POST':
        # --- التعديل الرئيسي هنا: نبحث عن "كل" المديرين وليس الأول فقط ---
        hr_profiles = Profile.objects.filter(user_type='HR Manager', user__is_superuser=False).select_related('user')
        
        subject = request.POST.get('subject', 'رسالة من موظف')
        body = request.POST.get('body', '')

        # إذا لم نجد أي مدير، نعرض رسالة خطأ
        if not hr_profiles.exists():
            messages.error(request, 'لا يوجد مدير موارد بشرية متاح حالياً لاستقبال الرسالة')
            return redirect('dashboard') # توجيه المستخدم إلى لوحة التحكم

        # --- نمر على كل مدير ونرسل له نسخة من الرسالة والإشعار ---
        for profile in hr_profiles:
            # إنشاء رسالة للمدير الحالي في الحلقة
            Message.objects.create(
                sender=request.user, 
                recipient=profile.user, 
                subject=subject, 
                body=body
            )
            # إنشاء إشعار للمدير الحالي في الحلقة
            Notification.objects.create(
                user=profile.user, 
                message=f'رسالة جديدة من الموظف: {request.user.get_full_name() or request.user.username}'
            )
            
        messages.success(request, 'تم إرسال رسالتك إلى قسم الموارد البشرية بنجاح')
        return redirect('dashboard') # توجيه المستخدم إلى لوحة التحكم بعد الإرسال

    # هذا الجزء يبقى كما هو لعرض الفورم
    return render(request, 'contact_hr.html')

@login_required
@user_passes_test(is_hr_manager)
def hr_inbox(request):
    msgs = Message.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'hr_inbox.html', {'messages': msgs})


@login_required
@user_passes_test(is_hr_manager)
def view_message(request, msg_id):
    msg = get_object_or_404(Message, id=msg_id, recipient=request.user)
    # mark as read
    if not msg.is_read:
        msg.is_read = True
        msg.save()
    return render(request, 'message_detail.html', {'message': msg})


@login_required
@user_passes_test(is_hr_manager)
def reply_message(request, msg_id):
    orig = get_object_or_404(Message, id=msg_id, recipient=request.user)
    if request.method == 'POST':
        body = request.POST.get('body', '')
        subject = 'رد: ' + (orig.subject or '')
        reply = Message.objects.create(sender=request.user, recipient=orig.sender, subject=subject, body=body, reply_to=orig)
        # notify the original sender (employee)
        Notification.objects.create(user=orig.sender, message=f'لقد تلقيت رداً من مدير الموارد البشرية: {request.user.username}', link='')
        messages.success(request, 'تم إرسال الرد')
        return redirect('hr_inbox')
    return render(request, 'reply_message.html', {'message': orig})


# ----------------------------
# Employee inbox and message thread (Employee views)
# ----------------------------


@login_required
@user_passes_test(is_employee)
def employee_inbox(request):
    """عرض صندوق الوارد الخاص بالموظف (الرسائل الواردة)"""
    msgs = Message.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'employee_inbox.html', {'messages': msgs})


@login_required
@user_passes_test(is_employee)
def employee_view_message(request, msg_id):
    """عرض رسالة محددة للموظف (وضع القراءة)"""
    msg = get_object_or_404(Message, id=msg_id, recipient=request.user)
    if not msg.is_read:
        msg.is_read = True
        msg.save()
    return render(request, 'employee_message_detail.html', {'message': msg})


@login_required
@user_passes_test(is_employee)
def employee_reply_message(request, msg_id):
    """تمكين الموظف من الرد على رسالة وصلته من مدير الموارد البشرية"""
    orig = get_object_or_404(Message, id=msg_id, recipient=request.user)
    if request.method == 'POST':
        body = request.POST.get('body', '')
        subject = 'رد: ' + (orig.subject or '')
        reply = Message.objects.create(sender=request.user, recipient=orig.sender, subject=subject, body=body, reply_to=orig)
        # notify the HR manager
        Notification.objects.create(user=orig.sender, message=f'لقد تلقيت رداً من الموظف: {request.user.username}', link='')
        messages.success(request, 'تم إرسال الرد إلى مدير الموارد البشرية')
        return redirect('employee_inbox')
    return render(request, 'employee_reply_message.html', {'message': orig})


# ----------------------------
# HR / Admin Management
# ----------------------------
@login_required
@user_passes_test(is_hr_manager)
def manage_employees(request):
    employees = Profile.objects.select_related('user').filter(user__is_superuser=False)
    return render(request, 'manage_employees.html', {'employees': employees})


@login_required
@user_passes_test(is_hr_manager)
def add_employee(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type', 'Employee')
        department = request.POST.get('department', '')
        if not username or not password:
            messages.error(request, 'الرجاء إدخال اسم مستخدم وكلمة مرور')
            return redirect('add_employee')
        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user, user_type=user_type, department=department)
        messages.success(request, 'تم إنشاء الموظف بنجاح')
        return redirect('manage_employees')
    return render(request, 'add_employee.html')


@login_required
@user_passes_test(is_hr_manager)
def edit_employee(request, emp_id):
    profile = get_object_or_404(Profile, id=emp_id)
    if request.method == 'POST':
        profile.phone = request.POST.get('phone')
        profile.qualification = request.POST.get('qualification')
        profile.address = request.POST.get('address')
        profile.user.email = request.POST.get('email')
        profile.user.first_name = request.POST.get('first_name', profile.user.first_name)
        profile.user.last_name = request.POST.get('last_name', profile.user.last_name)
        profile.user.save()
        profile.save()
        messages.success(request, 'تم تحديث بيانات الموظف')
        return redirect('manage_employees')
    return render(request, 'edit_employee.html', {'profile': profile})


@login_required
@user_passes_test(is_hr_manager)
def delete_employee(request, emp_id):
    profile = get_object_or_404(Profile, id=emp_id)
    profile.user.delete()
    messages.success(request, 'تم حذف الموظف')
    return redirect('manage_employees')


# ----------------------------
# Leave management (HR)
# ----------------------------
@login_required
@user_passes_test(is_hr_manager)
def manage_leaves(request):
    leaves = LeaveRequest.objects.select_related('employee__user').order_by('-start_date')
    return render(request, 'manage_leaves.html', {'leaves': leaves})


@login_required
@user_passes_test(is_hr_manager)
def approve_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    leave.status = 'Approved'
    leave.approved_by = request.user
    leave.save()
    messages.success(request, 'تم قبول الإجازة')
    return redirect('manage_leaves')


@login_required
@user_passes_test(is_hr_manager)
def reject_leave(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    leave.status = 'Rejected'
    leave.approved_by = request.user
    leave.save()
    messages.success(request, 'تم رفض الإجازة')
    return redirect('manage_leaves')


# ----------------------------
# Payroll & Evaluations
# ----------------------------
@login_required
@user_passes_test(lambda u: is_hr_manager(u) or is_finance(u))
def manage_payroll(request):
    payrolls = Payroll.objects.select_related('employee__user').all()
    return render(request, 'manage_payroll.html', {'payrolls': payrolls})


@login_required
@user_passes_test(lambda u: is_hr_manager(u) or is_finance(u))
def edit_payroll(request, pay_id):
    pay = get_object_or_404(Payroll, id=pay_id)
    if request.method == 'POST':
        # Safely convert inputs to Decimal to avoid string arithmetic
        def to_decimal(val, default):
            try:
                if val in (None, ''):
                    return default
                return Decimal(val)
            except (InvalidOperation, TypeError):
                return default

        pay.base_salary = to_decimal(request.POST.get('base_salary'), pay.base_salary)
        pay.bonuses = to_decimal(request.POST.get('bonuses'), pay.bonuses)
        pay.deductions = to_decimal(request.POST.get('deductions'), pay.deductions)
        pay.remarks = request.POST.get('remarks') or pay.remarks
        pay.save()
        messages.success(request, 'تم تحديث الرواتب')
        return redirect('manage_payroll')
    return render(request, 'edit_payroll.html', {'pay': pay})


# hr_app/views.py

# hr_app/views.py

@login_required
@user_passes_test(lambda u: is_hr_manager(u) or is_finance(u))
def add_payroll(request):
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        try:
            emp_id = request.POST.get('employee')
            # أضفت هنا معالجة للشهر والسنة لأنهما غير موجودين في الفورم حاليا
            # يمكنك إضافتهما للفورم أو استخدام القيمة الحالية كافتراضي
            month = timezone.now().month
            year = timezone.now().year

            base_salary = to_decimal(request.POST.get('base_salary'))
            bonuses = to_decimal(request.POST.get('bonuses'))
            deductions = to_decimal(request.POST.get('deductions'))
            remarks = request.POST.get('remarks')
            
            if not emp_id or base_salary is None:
                raise ValueError("Employee and Base Salary are required.")

            employee_profile = get_object_or_404(Profile, id=emp_id)

            # --- منع إضافة راتب لموظف لديه راتب بالفعل ---
            if Payroll.objects.filter(employee=employee_profile).exists():
                 if is_ajax:
                    return JsonResponse({'status': 'error', 'message': 'هذا الموظف لديه راتب مسجل بالفعل.'}, status=400)
                 else:
                    messages.error(request, 'هذا الموظف لديه راتب مسجل بالفعل.')
                    return redirect('add_payroll')


            new_payroll = Payroll.objects.create(
                employee=employee_profile,
                month=month,
                year=year,
                base_salary=base_salary,
                bonuses=bonuses,
                deductions=deductions,
                remarks=remarks
            )

            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'message': f'تمت إضافة الراتب للموظف {employee_profile.user.username} بنجاح.',
                    'employee_id': emp_id
                })
            else:
                messages.success(request, 'تمت إضافة الراتب بنجاح')
                return redirect('manage_payroll')

        except Exception as e:
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            else:
                messages.error(request, f'حدث خطأ: {str(e)}')
                return redirect('add_payroll')

    # هذا الجزء يبقى كما هو: جلب الموظفين الذين ليس لديهم راتب
    employees_with_no_payroll = Profile.objects.select_related('user').filter(payroll__isnull=True, user__is_superuser=False)
    return render(request, 'add_payroll.html', {'employees': employees_with_no_payroll})
@login_required
@user_passes_test(is_hr_manager)
def manage_evaluations(request):
    evaluations = Evaluation.objects.select_related('employee__user').all()
    return render(request, 'manage_evaluations.html', {'evaluations': evaluations})


@login_required
@user_passes_test(lambda u: is_finance(u) or is_hr_manager(u))
def export_payroll(request):
    """Export payrolls as CSV for finance/HR."""
    payrolls = Payroll.objects.select_related('employee__user').all().order_by('year', 'month')
    # Create the HttpResponse object with the appropriate CSV header.
    # Use UTF-8 with BOM so Excel on Windows opens Arabic text correctly.
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f'كشوفات_الرواتب_{timezone.now().date()}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Write UTF-8 BOM at the start so Excel recognizes UTF-8 encoding
    response.write('\ufeff')

    writer = csv.writer(response)
    # Header (Arabic)
    writer.writerow(['الموظف', 'السنة', 'الشهر', 'الراتب الأساسي', 'العلاوات', 'الخصومات', 'الصافي', 'ملاحظات'])
    for p in payrolls:
        writer.writerow([
            p.employee.user.username,
            p.year,
            p.month,
            str(p.base_salary),
            str(p.bonuses),
            str(p.deductions),
            str(p.net_salary),
            (p.remarks or '')
        ])
    return response


# hr_app/views.py

@login_required
@user_passes_test(is_hr_manager)
def add_evaluation(request): # <-- تم حذف emp_id من هنا
    if request.method == 'POST':
        # --- الآن سنحصل على emp_id من الفورم بدلاً من الرابط ---
        emp_id = request.POST.get('employee')
        score = request.POST.get('score')
        remarks = request.POST.get('remarks')
        month_str = request.POST.get('month')
        
        # التأكد من اختيار موظف
        if not emp_id:
            messages.error(request, "الرجاء اختيار الموظف المراد تقييمه.")
            # نحتاج لإعادة إرسال قائمة الموظفين مرة أخرى مع رسالة الخطأ
            employees_to_evaluate = Profile.objects.select_related('user').filter(user__is_superuser=False)
            return render(request, 'add_evaluation.html', {'employees': employees_to_evaluate})
        
        employee_profile = get_object_or_404(Profile, id=emp_id)
        evaluation_date = datetime.strptime(month_str, '%Y-%m').date()

        Evaluation.objects.create(
            employee=employee_profile,
            month=evaluation_date,
            score=score,
            remarks=remarks,
            evaluated_by=request.user
        )

        month_name = evaluation_date.strftime("%B %Y")
        Notification.objects.create(
            user=employee_profile.user,
            message=f"لقد تم تقييمك لشهر {month_name} من قبل المدير. يمكنك مراجعة التقييم في لوحة التحكم."
        )

        messages.success(request, f"تم إضافة التقييم للموظف {employee_profile.user.username} بنجاح.")
        # توجيه المستخدم إلى صفحة عرض التقييمات بعد النجاح
        return redirect('manage_evaluations')

    # --- في حالة GET: إرسال قائمة الموظفين إلى القالب ---
    employees_to_evaluate = Profile.objects.select_related('user').filter(user__is_superuser=False)
    context = {
        'employees': employees_to_evaluate
    }
    return render(request, 'add_evaluation.html', context)



# hr_app/views.py

# hr_app/views.py

# hr_app/views.py

# --- دالة مساعدة جديدة لتشغيل الكود غير المتزامن ---
# hr_app/views.py

async def generate_pdf_from_html(html_content, request):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # --- التصحيح هنا ---
        # 1. نقوم بتعيين محتوى الصفحة أولاً
        await page.set_content(html_content)

        # 2. ثم ننتظر حتى يتم تحميل كل شيء (مثل الخطوط) من الشبكة
        await page.wait_for_load_state('networkidle')
        
        pdf_bytes = await page.pdf(
            format='A4',
            print_background=True,
            margin={'top': '20mm', 'bottom': '20mm', 'left': '20mm', 'right': '20mm'}
        )
        await browser.close()
        return pdf_bytes
@login_required
@user_passes_test(lambda u: is_finance(u) or is_hr_manager(u))
def export_payroll_pdf(request):
    """
    تصدير كشوفات الرواتب كملف PDF باستخدام Playwright (الطريقة المضمونة).
    """
    payrolls = Payroll.objects.select_related('employee__user').all().order_by('employee__user__username')
    context = {
        'payrolls': payrolls,
        'export_date': timezone.now().strftime('%Y-%m-%d %H:%M'),
        'request': request # تمرير request مهم لتحميل الملفات الثابتة
    }
    
    # تحويل القالب إلى نص HTML
    html = render_to_string('payroll_pdf_template.html', context)
    
    # تشغيل الدالة غير المتزامنة وانتظار النتيجة
    pdf_file = asyncio.run(generate_pdf_from_html(html, request))

    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f'Payroll_Report_{timezone.now().date()}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response





# hr_app/views.py

@login_required
@user_passes_test(is_hr_manager)
def employee_details(request, emp_id):
    """
    عرض صفحة تفصيلية كاملة لملف الموظف وكل سجلاته للمدير.
    """
    # 1. جلب الملف الشخصي للموظف المحدد
    profile = get_object_or_404(Profile, id=emp_id)
    
    # 2. جلب كل السجلات المرتبطة بهذا الموظف
    # (نجلب آخر 10 سجلات فقط لتجنب إبطاء الصفحة)
    leaves = LeaveRequest.objects.filter(employee=profile).order_by('-start_date')[:10]
    attendances = Attendance.objects.filter(employee=profile).order_by('-date')[:10]
    
    # جلب آخر راتب مسجل
    payroll = Payroll.objects.filter(employee=profile).order_by('-year', '-month').first()
    
    # جلب آخر تقييم مسجل
    evaluation = Evaluation.objects.filter(employee=profile).order_by('-month').first()
    
    context = {
        'profile': profile,
        'leaves': leaves,
        'attendances': attendances,
        'payroll': payroll,
        'evaluation': evaluation,
    }
    
    return render(request, 'employee_details.html', context)