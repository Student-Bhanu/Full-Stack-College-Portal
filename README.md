# 🎓 College Management System

A full-stack web application for managing college operations with role-based access for **Admin**, **Teacher**, and **Student**. Built with Python (Flask) for the backend, MySQL for the database, and HTML/CSS/JavaScript for the frontend.

---

## 📌 Features

### 👨‍💼 Admin
- View and manage all students and teachers
- Restrict or activate student accounts
- View detailed student profiles (courses, attendance, results)
- View detailed teacher profiles (courses, enrolled students)
- Upload and manage exam results

### 👨‍🏫 Teacher
- View assigned courses and enrolled students
- Mark and update attendance (present/absent) for any date
- View attendance statistics with sorting and percentage filtering
- Create and delete assignments for courses
- Add or remove students from courses

### 👨‍🎓 Student
- View enrolled courses with teacher details
- Check attendance percentage per course
- View and submit assignments (with submission status)
- View exam scores filtered by semester

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Flask-CORS |
| Database | MySQL |
| Frontend | HTML, CSS, JavaScript |
| Auth | bcrypt (password hashing), Flask Sessions |

---

## 🗄️ Database Schema

The database (`college_db`) contains **10 normalized tables**:

```
admin               → Admin accounts
teacher             → Teacher accounts
student             → Student accounts (with active/restrict flag)
course              → Course catalog
teacher_course      → Teacher ↔ Course mapping
student_course      → Student ↔ Course enrollment
attendance          → Daily attendance records
assignment          → Assignments created by teachers
assignment_submission → Student submissions with grade & feedback
exam_score          → Semester exam results
```

---

## 📁 Project Structure

```
college-management-system/
│
├── app.py                    # Flask backend (all API routes)
├── schema.sql                # Database schema
├── data.sql                  # Sample data
│
├── index.html                # Landing / home page
├── login.html                # Login page (all roles)
├── admin_dashboard.html      # Admin panel
├── teacher_dashboard.html    # Teacher panel
├── student_dashboard.html    # Student panel
│
├── css/
│   └── style.css             # Shared styles
│
└── js/
    ├── index.js
    ├── login.js
    ├── admin_dashboard.js
    ├── teacher_dashboard.js
    └── student_dashboard.js
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.x
- MySQL Server
- pip

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/Student-Bhanu/Full-Stack-College-Portal.git
cd college-management-system
```

**2. Install Python dependencies**
```bash
pip install flask flask-cors mysql-connector-python bcrypt
```

**3. Set up the database**

Open MySQL and run:
```sql
source schema.sql
source data.sql
```

**4. Configure database connection**

In `app.py`, update the DB config with your MySQL credentials:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',   # change this
    'database': 'college_db'
}
```

Also change the Flask secret key:
```python
app.secret_key = 'your-secret-key'   # change this
```

**5. Run the application**
```bash
python app.py
```

Open your browser and go to: `http://127.0.0.1:5000`

---

## 🔐 Demo Login Credentials

| Role | Username | Password |
|---|---|---|
| Admin | admin | admin123 |
| Teacher | teacher1 | teacher123 |
| Student | student1 | student123 |

---

## 🔗 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/login` | Login (all roles) |
| POST | `/api/logout` | Logout |

### Student
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/student/courses` | Get enrolled courses |
| GET | `/api/student/attendance` | Get attendance records |
| GET/POST | `/api/student/assignments` | View / submit assignments |
| GET | `/api/student/scores` | View exam scores |

### Teacher
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/teacher/courses` | Get assigned courses |
| GET/POST | `/api/teacher/attendance` | View / mark attendance |
| GET | `/api/teacher/attendance/stats` | Attendance stats with filters |
| GET/POST/DELETE | `/api/teacher/assignments` | Manage assignments |
| GET/POST | `/api/teacher/students` | Manage course enrollments |

### Admin
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/admin/students` | View / add / restrict students |
| GET | `/api/admin/teachers` | View all teachers |
| GET | `/api/admin/courses` | View all courses |
| GET | `/api/admin/student/details` | Full student profile |
| GET | `/api/admin/teacher/details` | Full teacher profile |
| GET/POST | `/api/admin/results` | View / upload exam results |

---

## 👤 Author

**Bhanu Prabhat Suryavansham**  
B.Tech – Mathematics & Computing, Delhi Technological University  
GitHub: [github.com/Student-Bhanu](https://github.com/Student-Bhanu)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
