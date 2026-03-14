# HR Management Project

This is a Django-based HR management system. The project is configured to use MySQL in production via environment variables, but can be adapted for local development.

## Requirements
- Python 3.10+ (3.11 tested)
- MySQL server (or use another DB supported by Django)
- Recommended packages: see `requirements.txt`

## Install dependencies
Open PowerShell and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\hr_management\requirements.txt
```

Notes for Windows & mysqlclient:
- Installing `mysqlclient` on Windows requires Visual C++ Build Tools. If pip install fails, consider installing a pre-built wheel or use `pip install pymysql` and adjust settings (not included here).
- `Pillow` is required for ImageField support.

## Environment variables (MySQL)
Set these before running migrations or starting the server. In PowerShell you can run:

```powershell
$env:DB_ENGINE = 'django.db.backends.mysql'
$env:DB_NAME = 'hr_management_db'
$env:DB_USER = 'root'
$env:DB_PASSWORD = 'your_mysql_password'
$env:DB_HOST = '127.0.0.1'
$env:DB_PORT = '3306'
```

If you prefer to use SQLite for quick local testing, you can temporarily set `DB_ENGINE` to `'django.db.backends.sqlite3'` and `DB_NAME` to the path of the sqlite file.

## Create database (MySQL)
Using MySQL shell or Workbench, create the database and user and grant privileges. Example (MySQL CLI):

```sql
CREATE DATABASE hr_management_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'hr_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON hr_management_db.* TO 'hr_user'@'localhost';
FLUSH PRIVILEGES;
```

Then set `$env:DB_USER` and `$env:DB_PASSWORD` accordingly.

## Prepare and run project
From the repository root (where `manage.py` exists inside `hr_management`):

```powershell
# run migrations
python .\hr_management\manage.py makemigrations
python .\hr_management\manage.py migrate

# create superuser
python .\hr_management\manage.py createsuperuser

# run development server
python .\hr_management\manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Notes & Next steps
- Templates were refreshed to a modern RTL Bootstrap 5 look. If you want further visual changes (branding, colors, icons), I can continue.
- If MySQL installation or `mysqlclient` installation causes issues on Windows, tell me and I can switch instructions to `PyMySQL` or provide a Docker-based MySQL dev setup.
- Media files are served in development when `DEBUG=True`.

If you want, I can now:
- Run migrations on your behalf (I will need the DB accessible and env vars set), or
- Continue polishing other templates and add tests.

Tell me which of these (or both) you want me to do next.