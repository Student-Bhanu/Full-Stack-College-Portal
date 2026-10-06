# Student DBMS Management System

A Flask + MySQL student management project with separate student, teacher and admin dashboards.

## Features

- Student, teacher and admin login
- Student course, attendance, assignments and results
- Teacher course, attendance, assignments and student management
- Admin student and teacher management
- MySQL database with foreign keys
- Bcrypt password hashing
- Assignment file uploads

## Setup

1. Install Python 3.10+.
2. Create and activate a virtual environment:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

4. Create `.env ` and add your MySQL password and a secret key.
5. Run `schema.sql` in MySQL.
6. Run `data.sql` in MySQL.
7. Start the server:

```powershell
python app.py
```

8. Open `http://127.0.0.1:5000`.

## Demo credentials

- Admin: `admin` / `admin123`
- Teacher accounts: use any seeded teacher username / `pass123`
- Student accounts: use any seeded student username / `pass123`

Change these passwords before using the project outside a demo environment.
