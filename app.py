from datetime import datetime
from pathlib import Path
import os
import uuid

import bcrypt
import mysql.connector
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from mysql.connector import Error
from werkzeug.utils import secure_filename
from functools import wraps

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.getenv('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError('SECRET_KEY is missing. Create a .env file before starting the app.')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
CORS(app)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'college_db')
}

UPLOAD_FOLDER = Path(app.root_path) / 'uploads' / 'assignments'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'py', 'c', 'cpp', 'java', 'js', 'zip'}


def get_db_connection():
    if not DB_CONFIG['password']:
        print('DB_PASSWORD is missing. Add it to your .env file.')
        return None

    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f'Error connecting to MySQL: {e}')
        return None


def teacher_has_course(cursor, teacher_id, course_id):
    cursor.execute(
        'SELECT 1 FROM teacher_course WHERE teacher_id = %s AND course_id = %s',
        (teacher_id, course_id)
    )
    return cursor.fetchone() is not None


def student_has_course(cursor, student_id, course_id):
    cursor.execute(
        'SELECT 1 FROM student_course WHERE student_id = %s AND course_id = %s',
        (student_id, course_id)
    )
    return cursor.fetchone() is not None


def allowed_file(filename):
    return bool(
        filename and '.' in filename and
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def login_required(role=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 401
            if role and session.get('role') != role:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', '')

    if not username or not password or role not in {'student', 'teacher', 'admin'}:
        return jsonify({'success': False, 'message': 'Username, password and role are required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)

        tables = {
            'student': "SELECT student_id, username, password, name, email, roll_number, semester, department, is_active FROM student WHERE username = %s",
            'teacher': "SELECT teacher_id, username, password, name, email, department FROM teacher WHERE username = %s",
            'admin': "SELECT admin_id, username, password, email FROM admin WHERE username = %s"
        }
        cursor.execute(tables[role], (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        if role == 'student' and not user.get('is_active'):
            return jsonify({'success': False, 'message': 'Your account has been restricted. Contact admin.'}), 403

        try:
            password_valid = bcrypt.checkpw(
                password.encode('utf-8'),
                user['password'].encode('utf-8')
            )
        except (ValueError, TypeError):
            password_valid = False

        if not password_valid:
            return jsonify({'success': False, 'message': 'Invalid password'}), 401

        user_id_key = {
            'student': 'student_id',
            'teacher': 'teacher_id',
            'admin': 'admin_id'
        }[role]

        session.clear()
        session['user_id'] = user[user_id_key]
        session['username'] = user['username']
        session['role'] = role
        session['name'] = user.get('name', user['username'])

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'name': session['name'],
                'role': role,
                'semester': user.get('semester'),
                'department': user.get('department')
            }
        })
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/api/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@app.route('/api/student/attendance', methods=['GET'])
@login_required('student')
def student_attendance():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        student_id = session['user_id']
        course_id = request.args.get('course_id')

        if course_id:
            query = """
                SELECT a.attendance_date, a.status, c.course_name, c.course_code
                FROM attendance a
                JOIN course c ON a.course_id = c.course_id
                WHERE a.student_id = %s AND a.course_id = %s
                ORDER BY a.attendance_date DESC
            """
            cursor.execute(query, (student_id, course_id))
        else:
            query = """
                SELECT c.course_id, c.course_name, c.course_code,
                       SUM(a.status = 'Present') AS present_count,
                       COUNT(*) AS total_count
                FROM attendance a
                JOIN course c ON a.course_id = c.course_id
                WHERE a.student_id = %s
                GROUP BY c.course_id, c.course_name, c.course_code
                ORDER BY c.course_code
            """
            cursor.execute(query, (student_id,))

        return jsonify({'success': True, 'data': cursor.fetchall()})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/student/courses', methods=['GET'])
@login_required('student')
def student_courses():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT c.course_id, c.course_code, c.course_name, c.credits, c.semester,
                   t.name AS teacher_name, sc.enrollment_date
            FROM student_course sc
            JOIN course c ON sc.course_id = c.course_id
            LEFT JOIN teacher_course tc ON c.course_id = tc.course_id
            LEFT JOIN teacher t ON tc.teacher_id = t.teacher_id
            WHERE sc.student_id = %s
            ORDER BY c.semester, c.course_code
        """
        cursor.execute(query, (session['user_id'],))
        return jsonify({'success': True, 'data': cursor.fetchall()})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/student/assignments', methods=['GET', 'POST'])
@login_required('student')
def student_assignments():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    student_id = session['user_id']

    try:
        if request.method == 'GET':
            query = """
                SELECT a.assignment_id, a.title, a.description, a.due_date, a.created_at,
                       c.course_id, c.course_code, c.course_name,
                       CASE WHEN asub.submission_id IS NOT NULL THEN 'Submitted' ELSE 'Pending' END AS submission_status,
                       asub.submitted_at, asub.file_path
                FROM assignment a
                JOIN course c ON a.course_id = c.course_id
                JOIN student_course sc ON c.course_id = sc.course_id
                LEFT JOIN assignment_submission asub
                    ON a.assignment_id = asub.assignment_id AND asub.student_id = %s
                WHERE sc.student_id = %s
                ORDER BY a.due_date DESC
            """
            cursor.execute(query, (student_id, student_id))
            return jsonify({'success': True, 'data': cursor.fetchall()})

        assignment_id = request.form.get('assignment_id')
        uploaded_file = request.files.get('file')

        if not assignment_id or not uploaded_file:
            return jsonify({'success': False, 'message': 'Assignment ID and file are required'}), 400

        if not allowed_file(uploaded_file.filename):
            return jsonify({'success': False, 'message': 'File type is not allowed'}), 400

        cursor.execute(
            """SELECT a.assignment_id
               FROM assignment a
               JOIN student_course sc ON a.course_id = sc.course_id
               WHERE a.assignment_id = %s AND sc.student_id = %s""",
            (assignment_id, student_id)
        )
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'You are not enrolled in this assignment course'}), 403

        filename = f"{uuid.uuid4().hex}_{secure_filename(uploaded_file.filename)}"
        uploaded_file.save(UPLOAD_FOLDER / filename)
        file_path = f'/uploads/assignments/{filename}'

        cursor.execute(
            'SELECT submission_id FROM assignment_submission WHERE assignment_id = %s AND student_id = %s',
            (assignment_id, student_id)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """UPDATE assignment_submission
                   SET file_path = %s, submitted_at = NOW(), status = 'Submitted'
                   WHERE assignment_id = %s AND student_id = %s""",
                (file_path, assignment_id, student_id)
            )
        else:
            cursor.execute(
                """INSERT INTO assignment_submission (assignment_id, student_id, file_path)
                   VALUES (%s, %s, %s)""",
                (assignment_id, student_id, file_path)
            )

        conn.commit()
        return jsonify({'success': True, 'message': 'Assignment submitted successfully'})
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/student/scores', methods=['GET'])
@login_required('student')
def student_scores():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        semester = request.args.get('semester')
        query = """
            SELECT es.score_id, c.course_code, c.course_name, es.exam_type,
                   es.score, es.max_score, es.exam_date, es.semester
            FROM exam_score es
            JOIN course c ON es.course_id = c.course_id
            WHERE es.student_id = %s
        """
        params = [session['user_id']]
        if semester:
            query += ' AND es.semester = %s'
            params.append(semester)
        query += ' ORDER BY es.semester DESC, es.exam_date DESC'

        cursor.execute(query, tuple(params))
        return jsonify({'success': True, 'data': cursor.fetchall()})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/teacher/courses', methods=['GET'])
@login_required('teacher')
def teacher_courses():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT c.course_id, c.course_code, c.course_name, c.credits, c.semester, c.department,
                   COUNT(DISTINCT sc.student_id) AS enrolled_students
            FROM teacher_course tc
            JOIN course c ON tc.course_id = c.course_id
            LEFT JOIN student_course sc ON c.course_id = sc.course_id
            WHERE tc.teacher_id = %s
            GROUP BY c.course_id, c.course_code, c.course_name, c.credits, c.semester, c.department
            ORDER BY c.course_code
        """
        cursor.execute(query, (session['user_id'],))
        return jsonify({'success': True, 'data': cursor.fetchall()})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/teacher/attendance', methods=['GET', 'POST'])
@login_required('teacher')
def teacher_attendance():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    teacher_id = session['user_id']

    try:
        if request.method == 'GET':
            course_id = request.args.get('course_id')
            date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

            if course_id:
                if not teacher_has_course(cursor, teacher_id, course_id):
                    return jsonify({'success': False, 'message': 'Unauthorized access to this course'}), 403

                query = """
                    SELECT s.student_id, s.name, s.roll_number,
                           a.status AS attendance_status
                    FROM student_course sc
                    JOIN student s ON sc.student_id = s.student_id
                    LEFT JOIN attendance a
                        ON s.student_id = a.student_id
                       AND a.course_id = %s
                       AND a.attendance_date = %s
                    WHERE sc.course_id = %s AND s.is_active = TRUE
                    ORDER BY s.roll_number
                """
                cursor.execute(query, (course_id, date, course_id))
            else:
                query = """
                    SELECT c.course_id, c.course_code, c.course_name
                    FROM teacher_course tc
                    JOIN course c ON tc.course_id = c.course_id
                    WHERE tc.teacher_id = %s
                    ORDER BY c.course_code
                """
                cursor.execute(query, (teacher_id,))

            return jsonify({'success': True, 'data': cursor.fetchall()})

        data = request.get_json(silent=True) or {}
        student_id = data.get('student_id')
        course_id = data.get('course_id')
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        status = data.get('status')

        if not student_id or not course_id:
            return jsonify({'success': False, 'message': 'Student ID and Course ID required'}), 400
        if status not in {'Present', 'Absent'}:
            return jsonify({'success': False, 'message': 'Invalid attendance status'}), 400
        if not teacher_has_course(cursor, teacher_id, course_id):
            return jsonify({'success': False, 'message': 'Unauthorized access to this course'}), 403
        if not student_has_course(cursor, student_id, course_id):
            return jsonify({'success': False, 'message': 'Student is not enrolled in this course'}), 400

        cursor.execute(
            'SELECT attendance_id FROM attendance WHERE student_id = %s AND course_id = %s AND attendance_date = %s',
            (student_id, course_id, date)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                'UPDATE attendance SET status = %s, teacher_id = %s WHERE attendance_id = %s',
                (status, teacher_id, existing['attendance_id'])
            )
        else:
            cursor.execute(
                """INSERT INTO attendance
                   (student_id, course_id, teacher_id, attendance_date, status)
                   VALUES (%s, %s, %s, %s, %s)""",
                (student_id, course_id, teacher_id, date, status)
            )

        conn.commit()
        return jsonify({'success': True, 'message': 'Attendance marked successfully'})
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/teacher/attendance/stats', methods=['GET'])
@login_required('teacher')
def teacher_attendance_stats():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        teacher_id = session['user_id']
        course_id = request.args.get('course_id')
        sort_order = request.args.get('sort_order', 'desc').lower()
        min_percentage = request.args.get('min_percentage') or None
        max_percentage = request.args.get('max_percentage') or None

        if not course_id:
            return jsonify({'success': False, 'message': 'Course ID required'}), 400
        if not teacher_has_course(cursor, teacher_id, course_id):
            return jsonify({'success': False, 'message': 'Unauthorized access to this course'}), 403

        try:
            min_value = float(min_percentage) if min_percentage is not None else None
            max_value = float(max_percentage) if max_percentage is not None else None
        except ValueError:
            return jsonify({'success': False, 'message': 'Attendance filters must be numbers'}), 400

        query = """
            SELECT s.student_id, s.name, s.roll_number,
                   COUNT(a.attendance_id) AS total_classes,
                   COALESCE(SUM(a.status = 'Present'), 0) AS present_count,
                   COALESCE(SUM(a.status = 'Absent'), 0) AS absent_count,
                   CASE WHEN COUNT(a.attendance_id) > 0
                        THEN ROUND(SUM(a.status = 'Present') / COUNT(a.attendance_id) * 100, 2)
                        ELSE 0 END AS attendance_percentage
            FROM student_course sc
            JOIN student s ON sc.student_id = s.student_id
            LEFT JOIN attendance a
                ON s.student_id = a.student_id AND a.course_id = %s
            WHERE sc.course_id = %s AND s.is_active = TRUE
            GROUP BY s.student_id, s.name, s.roll_number
        """
        params = [course_id, course_id]

        if min_value is not None or max_value is not None:
            query += ' HAVING 1 = 1'
            if min_value is not None:
                query += ' AND attendance_percentage >= %s'
                params.append(min_value)
            if max_value is not None:
                query += ' AND attendance_percentage <= %s'
                params.append(max_value)

        query += ' ORDER BY attendance_percentage ' + ('ASC' if sort_order == 'asc' else 'DESC') + ', s.roll_number ASC'
        cursor.execute(query, tuple(params))
        return jsonify({'success': True, 'data': cursor.fetchall()})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/teacher/assignments', methods=['GET', 'POST', 'DELETE'])
@login_required('teacher')
def teacher_assignments():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    teacher_id = session['user_id']

    try:
        if request.method == 'GET':
            course_id = request.args.get('course_id')
            query = """
                SELECT a.assignment_id, a.title, a.description, a.due_date, a.created_at,
                       c.course_code, c.course_name
                FROM assignment a
                JOIN course c ON a.course_id = c.course_id
                WHERE a.teacher_id = %s
            """
            params = [teacher_id]
            if course_id:
                query += ' AND a.course_id = %s'
                params.append(course_id)
            query += ' ORDER BY a.due_date DESC'
            cursor.execute(query, tuple(params))
            return jsonify({'success': True, 'data': cursor.fetchall()})

        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            course_id = data.get('course_id')
            title = data.get('title', '').strip()
            description = data.get('description', '')
            due_date = data.get('due_date')

            if not course_id or not title:
                return jsonify({'success': False, 'message': 'Course ID and Title required'}), 400
            if not teacher_has_course(cursor, teacher_id, course_id):
                return jsonify({'success': False, 'message': 'Unauthorized access to this course'}), 403

            cursor.execute(
                """INSERT INTO assignment
                   (course_id, teacher_id, title, description, due_date)
                   VALUES (%s, %s, %s, %s, %s)""",
                (course_id, teacher_id, title, description, due_date)
            )
            conn.commit()
            return jsonify({'success': True, 'message': 'Assignment created successfully'})

        assignment_id = request.args.get('assignment_id')
        if not assignment_id:
            return jsonify({'success': False, 'message': 'Assignment ID required'}), 400

        cursor.execute(
            'DELETE FROM assignment WHERE assignment_id = %s AND teacher_id = %s',
            (assignment_id, teacher_id)
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'Assignment deleted successfully'})
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/teacher/students', methods=['GET', 'POST'])
@login_required('teacher')
def teacher_students():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    teacher_id = session['user_id']

    try:
        if request.method == 'GET':
            course_id = request.args.get('course_id')
            if course_id:
                if not teacher_has_course(cursor, teacher_id, course_id):
                    return jsonify({'success': False, 'message': 'Unauthorized access to this course'}), 403
                query = """
                    SELECT s.student_id, s.name, s.roll_number, s.email, s.semester, s.department
                    FROM student_course sc
                    JOIN student s ON sc.student_id = s.student_id
                    WHERE sc.course_id = %s AND s.is_active = TRUE
                    ORDER BY s.roll_number
                """
                cursor.execute(query, (course_id,))
            else:
                query = """
                    SELECT c.course_id, c.course_code, c.course_name
                    FROM teacher_course tc
                    JOIN course c ON tc.course_id = c.course_id
                    WHERE tc.teacher_id = %s
                    ORDER BY c.course_code
                """
                cursor.execute(query, (teacher_id,))
            return jsonify({'success': True, 'data': cursor.fetchall()})

        data = request.get_json(silent=True) or {}
        action = data.get('action')
        student_id = data.get('student_id')
        course_id = data.get('course_id')

        if action not in {'add', 'remove'} or not student_id or not course_id:
            return jsonify({'success': False, 'message': 'Invalid action or missing parameters'}), 400
        if not teacher_has_course(cursor, teacher_id, course_id):
            return jsonify({'success': False, 'message': 'Unauthorized access to this course'}), 403

        if action == 'add':
            query = """INSERT INTO student_course (student_id, course_id, enrollment_date)
                       VALUES (%s, %s, CURDATE())
                       ON DUPLICATE KEY UPDATE enrollment_date = CURDATE()"""
            message = 'Student added to course successfully'
        else:
            query = 'DELETE FROM student_course WHERE student_id = %s AND course_id = %s'
            message = 'Student removed from course successfully'

        cursor.execute(query, (student_id, course_id))
        conn.commit()
        return jsonify({'success': True, 'message': message})
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/students', methods=['GET', 'POST'])
@login_required('admin')
def admin_students():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        if request.method == 'GET':
            student_id = request.args.get('student_id')
            if student_id:
                query = """
                    SELECT s.*, GROUP_CONCAT(c.course_code) AS courses
                    FROM student s
                    LEFT JOIN student_course sc ON s.student_id = sc.student_id
                    LEFT JOIN course c ON sc.course_id = c.course_id
                    WHERE s.student_id = %s
                    GROUP BY s.student_id
                """
                cursor.execute(query, (student_id,))
            else:
                query = """
                    SELECT s.*, COUNT(DISTINCT sc.course_id) AS course_count,
                           GROUP_CONCAT(DISTINCT sc.course_id) AS course_ids
                    FROM student s
                    LEFT JOIN student_course sc ON s.student_id = sc.student_id
                    GROUP BY s.student_id
                    ORDER BY s.student_id DESC
                """
                cursor.execute(query)
            return jsonify({'success': True, 'data': cursor.fetchall()})

        data = request.get_json(silent=True) or {}
        action = data.get('action')

        if action == 'add':
            username = data.get('username', '').strip()
            password = data.get('password', 'student123')
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            roll_number = data.get('roll_number', '').strip()
            semester = data.get('semester', 1)
            department = data.get('department', '').strip()

            if not username or not name or not roll_number:
                return jsonify({'success': False, 'message': 'Username, name and roll number are required'}), 400

            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                """INSERT INTO student
                   (username, password, name, email, roll_number, semester, department)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (username, hashed, name, email, roll_number, semester, department)
            )
            conn.commit()
            return jsonify({'success': True, 'message': 'Student added successfully'})

        student_id = data.get('student_id')
        if not student_id:
            return jsonify({'success': False, 'message': 'Student ID required'}), 400

        if action == 'delete':
            cursor.execute('DELETE FROM student WHERE student_id = %s', (student_id,))
            conn.commit()
            return jsonify({'success': True, 'message': 'Student removed from database'})

        if action == 'restrict':
            is_active = bool(data.get('is_active'))
            cursor.execute('UPDATE student SET is_active = %s WHERE student_id = %s', (is_active, student_id))
            conn.commit()
            return jsonify({'success': True, 'message': 'Student access updated'})

        return jsonify({'success': False, 'message': 'Invalid action'}), 400
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/teachers', methods=['GET'])
@login_required('admin')
def admin_teachers():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        teacher_id = request.args.get('teacher_id')
        if teacher_id:
            query = """
                SELECT t.*, GROUP_CONCAT(DISTINCT c.course_code) AS courses_taught
                FROM teacher t
                LEFT JOIN teacher_course tc ON t.teacher_id = tc.teacher_id
                LEFT JOIN course c ON tc.course_id = c.course_id
                WHERE t.teacher_id = %s
                GROUP BY t.teacher_id
            """
            cursor.execute(query, (teacher_id,))
        else:
            query = """
                SELECT t.*, COUNT(DISTINCT tc.course_id) AS course_count,
                       COUNT(DISTINCT sc.student_id) AS student_count,
                       GROUP_CONCAT(DISTINCT c.course_code) AS courses_taught,
                       GROUP_CONCAT(DISTINCT c.course_id) AS course_ids,
                       GROUP_CONCAT(DISTINCT c.semester) AS course_semesters
                FROM teacher t
                LEFT JOIN teacher_course tc ON t.teacher_id = tc.teacher_id
                LEFT JOIN course c ON tc.course_id = c.course_id
                LEFT JOIN student_course sc ON c.course_id = sc.course_id
                GROUP BY t.teacher_id
                ORDER BY t.teacher_id DESC
            """
            cursor.execute(query)
        return jsonify({'success': True, 'data': cursor.fetchall()})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/courses', methods=['GET'])
@login_required('admin')
def admin_courses():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('SELECT course_id, course_code, course_name, semester FROM course ORDER BY semester, course_code')
        return jsonify({'success': True, 'data': cursor.fetchall()})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/student/details', methods=['GET'])
@login_required('admin')
def admin_student_details():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        student_id = request.args.get('student_id')
        if not student_id:
            return jsonify({'success': False, 'message': 'Student ID required'}), 400

        cursor.execute('SELECT * FROM student WHERE student_id = %s', (student_id,))
        student = cursor.fetchone()
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404

        cursor.execute("""
            SELECT c.course_id, c.course_code, c.course_name, c.credits, c.semester,
                   t.name AS teacher_name
            FROM student_course sc
            JOIN course c ON sc.course_id = c.course_id
            LEFT JOIN teacher_course tc ON c.course_id = tc.course_id
            LEFT JOIN teacher t ON tc.teacher_id = t.teacher_id
            WHERE sc.student_id = %s
            ORDER BY c.semester DESC, c.course_code
        """, (student_id,))
        courses = cursor.fetchall()

        cursor.execute("""
            SELECT c.course_id, c.course_code, c.course_name,
                   COUNT(a.attendance_id) AS total_classes,
                   COALESCE(SUM(a.status = 'Present'), 0) AS present_count,
                   COALESCE(SUM(a.status = 'Absent'), 0) AS absent_count,
                   CASE WHEN COUNT(a.attendance_id) > 0
                        THEN ROUND(SUM(a.status = 'Present') / COUNT(a.attendance_id) * 100, 2)
                        ELSE 0 END AS attendance_percentage
            FROM student_course sc
            JOIN course c ON sc.course_id = c.course_id
            LEFT JOIN attendance a ON sc.student_id = a.student_id AND sc.course_id = a.course_id
            WHERE sc.student_id = %s
            GROUP BY c.course_id, c.course_code, c.course_name
            ORDER BY c.course_code
        """, (student_id,))
        attendance = cursor.fetchall()

        cursor.execute("""
            SELECT es.*, c.course_code, c.course_name
            FROM exam_score es
            JOIN course c ON es.course_id = c.course_id
            WHERE es.student_id = %s
            ORDER BY es.semester DESC, es.exam_date DESC
        """, (student_id,))
        results = cursor.fetchall()

        return jsonify({'success': True, 'data': {
            'student': student,
            'courses': courses,
            'attendance': attendance,
            'results': results
        }})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/teacher/details', methods=['GET'])
@login_required('admin')
def admin_teacher_details():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        teacher_id = request.args.get('teacher_id')
        if not teacher_id:
            return jsonify({'success': False, 'message': 'Teacher ID required'}), 400

        cursor.execute('SELECT * FROM teacher WHERE teacher_id = %s', (teacher_id,))
        teacher = cursor.fetchone()
        if not teacher:
            return jsonify({'success': False, 'message': 'Teacher not found'}), 404

        cursor.execute("""
            SELECT c.course_id, c.course_code, c.course_name, c.credits, c.semester,
                   COUNT(DISTINCT sc.student_id) AS enrolled_students
            FROM teacher_course tc
            JOIN course c ON tc.course_id = c.course_id
            LEFT JOIN student_course sc ON c.course_id = sc.course_id
            WHERE tc.teacher_id = %s
            GROUP BY c.course_id, c.course_code, c.course_name, c.credits, c.semester
            ORDER BY c.semester, c.course_code
        """, (teacher_id,))
        courses = cursor.fetchall()

        students_by_course = {}
        for course in courses:
            cursor.execute("""
                SELECT s.student_id, s.name, s.roll_number, s.email, s.semester
                FROM student_course sc
                JOIN student s ON sc.student_id = s.student_id
                WHERE sc.course_id = %s AND s.is_active = TRUE
                ORDER BY s.roll_number
            """, (course['course_id'],))
            students_by_course[course['course_id']] = cursor.fetchall()

        return jsonify({'success': True, 'data': {
            'teacher': teacher,
            'courses': courses,
            'students_by_course': students_by_course
        }})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/results', methods=['GET', 'POST'])
@login_required('admin')
def admin_results():
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = conn.cursor(dictionary=True)

    try:
        if request.method == 'GET':
            semester = request.args.get('semester')
            student_id = request.args.get('student_id')
            query = """
                SELECT es.*, c.course_code, c.course_name,
                       s.name AS student_name, s.roll_number
                FROM exam_score es
                JOIN course c ON es.course_id = c.course_id
                JOIN student s ON es.student_id = s.student_id
            """
            params = []
            if student_id:
                query += ' WHERE es.student_id = %s'
                params.append(student_id)
            elif semester:
                query += ' WHERE es.semester = %s'
                params.append(semester)
            query += ' ORDER BY es.semester DESC, s.roll_number, c.course_code'
            cursor.execute(query, tuple(params))
            return jsonify({'success': True, 'data': cursor.fetchall()})

        data = request.get_json(silent=True) or {}
        student_id = data.get('student_id')
        course_id = data.get('course_id')
        semester = data.get('semester')
        exam_type = data.get('exam_type')
        score = data.get('score')
        max_score = data.get('max_score', 100)
        exam_date = data.get('exam_date')

        if any(value in (None, '') for value in [student_id, course_id, semester, exam_type, score, exam_date]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        try:
            score_value = float(score)
            max_score_value = float(max_score)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Score and max score must be numbers'}), 400

        if max_score_value <= 0 or score_value < 0 or score_value > max_score_value:
            return jsonify({'success': False, 'message': 'Invalid score values'}), 400

        cursor.execute(
            """INSERT INTO exam_score
               (student_id, course_id, semester, exam_type, score, max_score, exam_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (student_id, course_id, semester, exam_type, score_value, max_score_value, exam_date)
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'Result uploaded successfully'})
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/uploads/assignments/<path:filename>')
@login_required()
def download_assignment(filename):
    cursor = None
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        file_path = f'/uploads/assignments/{filename}'
        cursor.execute(
            'SELECT student_id FROM assignment_submission WHERE file_path = %s',
            (file_path,)
        )
        submission = cursor.fetchone()

        if not submission:
            return jsonify({'success': False, 'message': 'File not found'}), 404

        if session.get('role') == 'student' and submission['student_id'] != session['user_id']:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    finally:
        if cursor:
            cursor.close()
        conn.close()


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    if path.startswith('api/') or path.startswith('uploads/'):
        return jsonify({'error': 'Not found'}), 404
    return send_from_directory('.', path)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
