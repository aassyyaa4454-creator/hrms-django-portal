from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# ----------------------------
# نموذج Profile لتحديد نوع المستخدم
# ----------------------------
class Profile(models.Model):
    USER_TYPES = (
        ('HR Manager', 'HR Manager'),
        ('Employee', 'Employee'),
        ('Finance', 'Finance'),
    )
    DEPARTMENTS = (
        ('HR', 'HR'),
        ('Finance', 'Finance'),
        ('IT', 'IT'),
        ('Sales', 'Sales'),
        ('Operations', 'Operations'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    department = models.CharField(max_length=50, choices=DEPARTMENTS, blank=True, null=True)
    date_joined = models.DateField(default=timezone.now)

    # الحقول الإضافية للملف الشخصي
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    qualification = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"


# ----------------------------
# نموذج حضور الموظف
# ----------------------------
class Attendance(models.Model):
    STATUS_CHOICES = (
        ('Present', 'حاضر'),
        ('Absent', 'غائب'),
        ('Late', 'متأخر'),
    )
    employee = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')

    def __str__(self):
        return f"{self.employee.user.username} - {self.date}"


# ----------------------------
# نموذج طلب الإجازة
# ----------------------------
class LeaveRequest(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'معلق'),
        ('Approved', 'مقبول'),
        ('Rejected', 'مرفوض'),
    )
    LEAVE_TYPES = (
        ('Sick', 'مرضية'),
        ('Annual', 'سنوية'),
        ('Emergency', 'طارئة'),
    )
    employee = models.ForeignKey(Profile, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')

    def __str__(self):
        return f"{self.employee.user.username} - {self.leave_type}"


# ----------------------------
# نموذج الرواتب
# ----------------------------
class Payroll(models.Model):
    employee = models.ForeignKey(Profile, on_delete=models.CASCADE)
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.net_salary = self.base_salary + self.bonuses - self.deductions
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.user.username} - {self.month}/{self.year} - {self.net_salary}"


# ----------------------------
# نموذج التقييم
# ----------------------------
class Evaluation(models.Model):
    employee = models.ForeignKey(Profile, on_delete=models.CASCADE)
    month = models.DateField()
    score = models.DecimalField(max_digits=5, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)
    evaluated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='evaluations_given')

    def __str__(self):
        return f"{self.employee.user.username} - {self.month}"


# ----------------------------
# نموذج الإشعارات
# ----------------------------
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.message[:20]}"


# ----------------------------
# نموذج الرسائل الداخلية بين المستخدمين
# ----------------------------
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.subject[:30]}"
