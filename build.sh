#!/usr/bin/env bash
# exit on error
set -o errexit

# تنصيب المكتبات
pip install -r requirements.txt

# تجميع ملفات التنسيق CSS/JS
python manage.py collectstatic --no-input

# بناء جداول قاعدة البيانات
python manage.py migrate

# إنشاء السوبر يوزر تلقائياً (بناءً على معلومات سنضعها في ريندر بعد قليل)
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