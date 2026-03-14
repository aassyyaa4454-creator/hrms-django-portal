#!/usr/bin/env bash
# exit on error
set -o errexit

# تنصيب المكتبات
pip install -r requirements.txt

# تنصيب متصفح بلاي رايت (ضروري لأن مشروعك يستدعي المكتبة في views.py)
python -m playwright install --with-deps chromium

# تجميع الملفات الثابتة
python manage.py collectstatic --no-input

# عمل الهجرة لقاعدة البيانات
python manage.py migrate

# إنشاء السوبر يوزر تلقائياً من المتغيرات التي وضعناها في ريندر
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
