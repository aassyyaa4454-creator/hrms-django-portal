from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Attendance, LeaveRequest, Payroll, Evaluation, Notification

# Inline لإظهار Profile عند User
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

# تمديد UserAdmin لإظهار Profile
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

# إزالة User الافتراضي وإعادة تسجيله مع التعديل
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# تسجيل باقي النماذج
admin.site.register(Attendance)
admin.site.register(LeaveRequest)
admin.site.register(Payroll)
admin.site.register(Evaluation)
admin.site.register(Notification)
