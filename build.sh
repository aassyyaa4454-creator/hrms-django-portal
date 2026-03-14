#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. تنصيب المكتبات
pip install -r requirements.txt

# 2. تنصيب متصفح بلاي رايت (بدون --with-deps لتجنب طلب صلاحيات السوبر يوزر)
python -m playwright install chromium

# 3. تجميع الملفات الثابتة
python manage.py collectstatic --no-input

# 4. عمل الهجرة لقاعدة البيانات
python manage.py migrate

# 5. إنشاء السوبر يوزر تلقائياً
if [ "$CREATE_SUPERUSER" ]; then
  python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="$DJANGO_SUPERUSER_USERNAME").exists():
    User.objects.create_superuser("$DJANGO_SUPERUSER_USERNAME", "$DJANGO_SUPERUSER_EMAIL", "$DJANGO_SUPERUSER_PASSWORD")
    print("Superuser created successfully")
else:
    print("Superuser already exists")
END
fi
