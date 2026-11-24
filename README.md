# Smart Scholarship Management System (SSMS)

Web-based application built with **Python, Django, Django ORM, SQLite, HTML5, CSS3, JavaScript, and Bootstrap 5**.

## Quick Start (Windows PowerShell)

1. Open this folder (`smart_scholarship_system`) in VS Code.
2. Create and activate virtual environment:
   ```powershell
   py -m venv venv
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Apply database migrations and create an Admin user:
   ```powershell
   py manage.py makemigrations scholarships
   py manage.py migrate
   py manage.py createsuperuser
   ```
5. Start the server:
   ```powershell
   py manage.py runserver
   ```
6. Open `http://127.0.0.1:8000/` in your browser.
