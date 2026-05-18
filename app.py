from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from functools import wraps
import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import datetime
import os

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = 'your-secret-key-change-in-production'  # Change this in production
CORS(app)  # Enable CORS for all routes

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'King915378@.',
    'database': 'college_db'
}

def get_db_connection():
    """Create and return database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def login_required(role=None):
    """Decorator to check if user is logged in and has correct role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 401
            if role and session.get('role') != role:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/api/login', methods=['POST'])
def login():
    """Handle user login"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    role = data.get('role', '')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Determine table based on role
        if role == 'student':
            query = "SELECT student_id, username, password, name, email, roll_number, semester, department, is_active FROM student WHERE username = %s"
        elif role == 'teacher':
            query = "SELECT teacher_id, username, password, name, email, department FROM teacher WHERE username = %s"
        elif role == 'admin':
            query = "SELECT admin_id, username, password, email FROM admin WHERE username = %s"
        else:
            return jsonify({'success': False, 'message': 'Invalid role'}), 400
        
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Check if student is active
        if role == 'student' and not user.get('is_active'):
            return jsonify({'success': False, 'message': 'Your account has been restricted. Contact admin.'}), 403
        
        # Verify password
        password_valid = False
        if user['password'].startswith('$2'):  # Bcrypt hash
            password_valid = bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))
        
        # Demo passwords for testing
        demo_passwords = ['admin123', 'teacher123', 'student123']
        if not password_valid and password in demo_passwords:
            password_valid = True
        
        if password_valid:
            # Set session
            user_id_key = 'student_id' if role == 'student' else ('teacher_id' if role == 'teacher' else 'admin_id')
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
                    'role': role
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid password'}), 401
            
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/logout', methods=['POST', 'GET'])
def logout():
    """Handle user logout"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# ==================== STUDENT ROUTES ====================

@app.route('/api/student/attendance', methods=['GET'])
@login_required(role='student')
def student_attendance():
    """Get student attendance records"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
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
                SELECT a.attendance_date, a.status, c.course_name, c.course_code, c.course_id,
                       SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
                       COUNT(*) as total_count
                FROM attendance a
                JOIN course c ON a.course_id = c.course_id
                WHERE a.student_id = %s
                GROUP BY c.course_id, c.course_name, c.course_code
                ORDER BY c.course_code
            """
            cursor.execute(query, (student_id,))
        
        attendance = cursor.fetchall()
        return jsonify({'success': True, 'data': attendance})
        
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/student/courses', methods=['GET'])
@login_required(role='student')
def student_courses():
    """Get student enrolled courses"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        student_id = session['user_id']
        
        query = """
            SELECT c.course_id, c.course_code, c.course_name, c.credits, c.semester, 
                   t.name as teacher_name, sc.enrollment_date
            FROM student_course sc
            JOIN course c ON sc.course_id = c.course_id
            LEFT JOIN teacher_course tc ON c.course_id = tc.course_id
            LEFT JOIN teacher t ON tc.teacher_id = t.teacher_id
            WHERE sc.student_id = %s
            ORDER BY c.semester, c.course_code
        """
        cursor.execute(query, (student_id,))
        courses = cursor.fetchall()
        
        return jsonify({'success': True, 'data': courses})
        
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/student/assignments', methods=['GET', 'POST'])
@login_required(role='student')
def student_assignments():
    """Get or submit student assignments"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        student_id = session['user_id']
        
        if request.method == 'GET':
            query = """
                SELECT a.assignment_id, a.title, a.description, a.due_date, a.created_at,
                       c.course_id, c.course_code, c.course_name,
                       CASE WHEN asub.submission_id IS NOT NULL THEN 'Submitted' ELSE 'Pending' END as submission_status,
                       asub.submitted_at
                FROM assignment a
                JOIN course c ON a.course_id = c.course_id
                JOIN student_course sc ON c.course_id = sc.course_id
                LEFT JOIN assignment_submission asub ON a.assignment_id = asub.assignment_id AND asub.student_id = %s
                WHERE sc.student_id = %s
                ORDER BY a.due_date DESC
            """
            cursor.execute(query, (student_id, student_id))
            assignments = cursor.fetchall()
            return jsonify({'success': True, 'data': assignments})
        
        elif request.method == 'POST':
            data = request.get_json()
            assignment_id = data.get('assignment_id')
            file_path = data.get('file_path', '')
            
            if not assignment_id:
                return jsonify({'success': False, 'message': 'Assignment ID required'}), 400
            
            # Check if already submitted
            check_query = "SELECT submission_id FROM assignment_submission WHERE assignment_id = %s AND student_id = %s"
            cursor.execute(check_query, (assignment_id, student_id))
            existing = cursor.fetchone()
            
            if existing:
                update_query = "UPDATE assignment_submission SET file_path = %s, submitted_at = NOW() WHERE assignment_id = %s AND student_id = %s"
                cursor.execute(update_query, (file_path, assignment_id, student_id))
            else:
                insert_query = "INSERT INTO assignment_submission (assignment_id, student_id, file_path) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (assignment_id, student_id, file_path))
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Assignment submitted successfully'})
        
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/student/scores', methods=['GET'])
@login_required(role='student')
def student_scores():
    """Get student exam scores"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        student_id = session['user_id']
        semester = request.args.get('semester')
        
        if semester:
            query = """
                SELECT es.score_id, c.course_code, c.course_name, es.exam_type, 
                       es.score, es.max_score, es.exam_date, es.semester
                FROM exam_score es
                JOIN course c ON es.course_id = c.course_id
                WHERE es.student_id = %s AND es.semester = %s
                ORDER BY es.exam_date DESC
            """
            cursor.execute(query, (student_id, semester))
        else:
            query = """
                SELECT es.score_id, c.course_code, c.course_name, es.exam_type, 
                       es.score, es.max_score, es.exam_date, es.semester
                FROM exam_score es
                JOIN course c ON es.course_id = c.course_id
                WHERE es.student_id = %s
                ORDER BY es.semester DESC, es.exam_date DESC
            """
            cursor.execute(query, (student_id,))
        
        scores = cursor.fetchall()
        return jsonify({'success': True, 'data': scores})
        
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ==================== TEACHER ROUTES ====================

@app.route('/api/teacher/courses', methods=['GET'])
@login_required(role='teacher')
def teacher_courses():
    """Get courses taught by teacher"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        teacher_id = session['user_id']
        
        query = """
            SELECT c.course_id, c.course_code, c.course_name, c.credits, c.semester, c.department,
                   COUNT(DISTINCT sc.student_id) as enrolled_students
            FROM teacher_course tc
            JOIN course c ON tc.course_id = c.course_id
            LEFT JOIN student_course sc ON c.course_id = sc.course_id
            WHERE tc.teacher_id = %s
            GROUP BY c.course_id, c.course_code, c.course_name, c.credits, c.semester, c.department
            ORDER BY c.course_code
        """
        cursor.execute(query, (teacher_id,))
        courses = cursor.fetchall()
        
        return jsonify({'success': True, 'data': courses})
        
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/teacher/attendance', methods=['GET', 'POST'])
@login_required(role='teacher')
def teacher_attendance():
    """Get students for attendance or mark attendance"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        teacher_id = session['user_id']
        
        if request.method == 'GET':
            course_id = request.args.get('course_id')
            date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            if course_id:
                query = """
                    SELECT s.student_id, s.name, s.roll_number,
                           CASE WHEN a.attendance_id IS NOT NULL THEN a.status ELSE NULL END as attendance_status
                    FROM student_course sc
                    JOIN student s ON sc.student_id = s.student_id
                    LEFT JOIN attendance a ON s.student_id = a.student_id AND a.course_id = %s AND a.attendance_date = %s
                    WHERE sc.course_id = %s AND s.is_active = TRUE
                    ORDER BY s.roll_number
                """
                cursor.execute(query, (course_id, date, course_id))
            else:
                query = """
                    SELECT DISTINCT c.course_id, c.course_code, c.course_name
                    FROM teacher_course tc
                    JOIN course c ON tc.course_id = c.course_id
                    WHERE tc.teacher_id = %s
                    ORDER BY c.course_code
                """
                cursor.execute(query, (teacher_id,))
            
            data = cursor.fetchall()
            return jsonify({'success': True, 'data': data})
        
        elif request.method == 'POST':
            data = request.get_json()
            student_id = data.get('student_id')
            course_id = data.get('course_id')
            date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
            status = data.get('status', 'Present')
            
            if not student_id or not course_id:
                return jsonify({'success': False, 'message': 'Student ID and Course ID required'}), 400
            
            # Check if attendance already exists
            check_query = "SELECT attendance_id FROM attendance WHERE student_id = %s AND course_id = %s AND attendance_date = %s"
            cursor.execute(check_query, (student_id, course_id, date))
            existing = cursor.fetchone()
            
            if existing:
                update_query = "UPDATE attendance SET status = %s WHERE student_id = %s AND course_id = %s AND attendance_date = %s"
                cursor.execute(update_query, (status, student_id, course_id, date))
            else:
                insert_query = "INSERT INTO attendance (student_id, course_id, teacher_id, attendance_date, status) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(insert_query, (student_id, course_id, teacher_id, date, status))
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Attendance marked successfully'})
        
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/teacher/attendance/stats', methods=['GET'])
@login_required(role='teacher')
def teacher_attendance_stats():
    """Get attendance statistics for students in a course with sorting and filtering"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        teacher_id = session['user_id']
        course_id = request.args.get('course_id')
        sort_order = request.args.get('sort_order', 'desc')  # 'asc' or 'desc'
        min_percentage = request.args.get('min_percentage')
        max_percentage = request.args.get('max_percentage')
        
        # Convert empty strings to None
        if min_percentage == '':
            min_percentage = None
        if max_percentage == '':
            max_percentage = None
        
        if not course_id:
            return jsonify({'success': False, 'message': 'Course ID required'}), 400
        
        # Verify teacher teaches this course
        verify_query = "SELECT course_id FROM teacher_course WHERE teacher_id = %s AND course_id = %s"
        cursor.execute(verify_query, (teacher_id, course_id))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Unauthorized access to this course'}), 403
        
        # Calculate attendance statistics for each student
        query = """
            SELECT s.student_id, s.name, s.roll_number,
                   COUNT(a.attendance_id) as total_classes,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
                   SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count,
                   CASE 
                       WHEN COUNT(a.attendance_id) > 0 
                       THEN ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.attendance_id)) * 100, 2)
                       ELSE 0 
                   END as attendance_percentage
            FROM student_course sc
            JOIN student s ON sc.student_id = s.student_id
            LEFT JOIN attendance a ON s.student_id = a.student_id AND a.course_id = %s
            WHERE sc.course_id = %s AND s.is_active = TRUE
            GROUP BY s.student_id, s.name, s.roll_number
        """
        
        # Add filtering by attendance range
        if min_percentage is not None or max_percentage is not None:
            query += " HAVING 1=1"
            if min_percentage is not None:
                query += " AND attendance_percentage >= %s"
            if max_percentage is not None:
                query += " AND attendance_percentage <= %s"
        
        # Add sorting
        if sort_order.lower() == 'asc':
            query += " ORDER BY attendance_percentage ASC, s.roll_number ASC"
        else:
            query += " ORDER BY attendance_percentage DESC, s.roll_number ASC"
        
        # Execute query with parameters
        params = [course_id, course_id]
        if min_percentage is not None:
            params.append(float(min_percentage))
        if max_percentage is not None:
            params.append(float(max_percentage))
        
        cursor.execute(query, tuple(params))
        data = cursor.fetchall()
        
        return jsonify({'success': True, 'data': data})
        
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/teacher/assignments', methods=['GET', 'POST', 'DELETE'])
@login_required(role='teacher')
def teacher_assignments():
    """Get, create, or delete assignments"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        teacher_id = session['user_id']
        
        if request.method == 'GET':
            course_id = request.args.get('course_id')
            
            if course_id:
                query = """
                    SELECT a.assignment_id, a.title, a.description, a.due_date, a.created_at,
                           c.course_code, c.course_name
                    FROM assignment a
                    JOIN course c ON a.course_id = c.course_id
                    WHERE a.teacher_id = %s AND a.course_id = %s
                    ORDER BY a.due_date DESC
                """
                cursor.execute(query, (teacher_id, course_id))
            else:
                query = """
                    SELECT a.assignment_id, a.title, a.description, a.due_date, a.created_at,
                           c.course_code, c.course_name
                    FROM assignment a
                    JOIN course c ON a.course_id = c.course_id
                    WHERE a.teacher_id = %s
                    ORDER BY a.due_date DESC
                """
                cursor.execute(query, (teacher_id,))
            
            assignments = cursor.fetchall()
            return jsonify({'success': True, 'data': assignments})
        
        elif request.method == 'POST':
            data = request.get_json()
            course_id = data.get('course_id')
            title = data.get('title', '')
            description = data.get('description', '')
            due_date = data.get('due_date')
            
            if not course_id or not title:
                return jsonify({'success': False, 'message': 'Course ID and Title required'}), 400
            
            insert_query = "INSERT INTO assignment (course_id, teacher_id, title, description, due_date) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (course_id, teacher_id, title, description, due_date))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Assignment created successfully'})
        
        elif request.method == 'DELETE':
            assignment_id = request.args.get('assignment_id')
            
            if not assignment_id:
                return jsonify({'success': False, 'message': 'Assignment ID required'}), 400
            
            delete_query = "DELETE FROM assignment WHERE assignment_id = %s AND teacher_id = %s"
            cursor.execute(delete_query, (assignment_id, teacher_id))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Assignment deleted successfully'})
        
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/teacher/students', methods=['GET', 'POST'])
@login_required(role='teacher')
def teacher_students():
    """Get students in course or add/remove students"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        teacher_id = session['user_id']
        
        if request.method == 'GET':
            course_id = request.args.get('course_id')
            
            if course_id:
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
                    SELECT DISTINCT c.course_id, c.course_code, c.course_name
                    FROM teacher_course tc
                    JOIN course c ON tc.course_id = c.course_id
                    WHERE tc.teacher_id = %s
                    ORDER BY c.course_code
                """
                cursor.execute(query, (teacher_id,))
            
            data = cursor.fetchall()
            return jsonify({'success': True, 'data': data})
        
        elif request.method == 'POST':
            data = request.get_json()
            action = data.get('action')
            student_id = data.get('student_id')
            course_id = data.get('course_id')
            
            if action == 'add' and student_id and course_id:
                insert_query = "INSERT INTO student_course (student_id, course_id, enrollment_date) VALUES (%s, %s, CURDATE()) ON DUPLICATE KEY UPDATE enrollment_date = CURDATE()"
                cursor.execute(insert_query, (student_id, course_id))
                conn.commit()
                return jsonify({'success': True, 'message': 'Student added to course successfully'})
            
            elif action == 'remove' and student_id and course_id:
                delete_query = "DELETE FROM student_course WHERE student_id = %s AND course_id = %s"
                cursor.execute(delete_query, (student_id, course_id))
                conn.commit()
                return jsonify({'success': True, 'message': 'Student removed from course successfully'})
            
            else:
                return jsonify({'success': False, 'message': 'Invalid action or missing parameters'}), 400
        
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ==================== ADMIN ROUTES ====================

@app.route('/api/admin/students', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_students():
    """Get all students or manage students"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'GET':
            student_id = request.args.get('student_id')
            
            if student_id:
                query = """
                    SELECT s.*, GROUP_CONCAT(c.course_code) as courses
                    FROM student s
                    LEFT JOIN student_course sc ON s.student_id = sc.student_id
                    LEFT JOIN course c ON sc.course_id = c.course_id
                    WHERE s.student_id = %s
                    GROUP BY s.student_id
                """
                cursor.execute(query, (student_id,))
            else:
                query = """
                    SELECT s.*, COUNT(DISTINCT sc.course_id) as course_count
                    FROM student s
                    LEFT JOIN student_course sc ON s.student_id = sc.student_id
                    GROUP BY s.student_id
                    ORDER BY s.student_id DESC
                """
                cursor.execute(query)
            
            students = cursor.fetchall()
            return jsonify({'success': True, 'data': students})
        
        elif request.method == 'POST':
            data = request.get_json()
            action = data.get('action')
            
            if action == 'add':
                username = data.get('username', '')
                password = data.get('password', 'student123')
                name = data.get('name', '')
                email = data.get('email', '')
                roll_number = data.get('roll_number', '')
                semester = data.get('semester', 1)
                department = data.get('department', '')
                
                # Hash password
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                insert_query = "INSERT INTO student (username, password, name, email, roll_number, semester, department) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(insert_query, (username, hashed, name, email, roll_number, semester, department))
                conn.commit()
                return jsonify({'success': True, 'message': 'Student added successfully'})
            
            elif action == 'delete':
                student_id = data.get('student_id')
                if student_id:
                    delete_query = "DELETE FROM student WHERE student_id = %s"
                    cursor.execute(delete_query, (student_id,))
                    conn.commit()
                    return jsonify({'success': True, 'message': 'Student removed from database'})
            
            elif action == 'restrict':
                student_id = data.get('student_id')
                is_active = data.get('is_active', False)
                if student_id:
                    update_query = "UPDATE student SET is_active = %s WHERE student_id = %s"
                    cursor.execute(update_query, (is_active, student_id))
                    conn.commit()
                    return jsonify({'success': True, 'message': 'Student access updated'})
        
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/admin/teachers', methods=['GET'])
@login_required(role='admin')
def admin_teachers():
    """Get all teachers and their courses"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        teacher_id = request.args.get('teacher_id')
        
        if teacher_id:
            query = """
                SELECT t.*, GROUP_CONCAT(c.course_code) as courses_taught
                FROM teacher t
                LEFT JOIN teacher_course tc ON t.teacher_id = tc.teacher_id
                LEFT JOIN course c ON tc.course_id = c.course_id
                WHERE t.teacher_id = %s
                GROUP BY t.teacher_id
            """
            cursor.execute(query, (teacher_id,))
        else:
            query = """
                SELECT t.*, COUNT(DISTINCT tc.course_id) as course_count,
                       GROUP_CONCAT(DISTINCT c.course_code) as courses_taught
                FROM teacher t
                LEFT JOIN teacher_course tc ON t.teacher_id = tc.teacher_id
                LEFT JOIN course c ON tc.course_id = c.course_id
                GROUP BY t.teacher_id
                ORDER BY t.teacher_id DESC
            """
            cursor.execute(query)
        
        teachers = cursor.fetchall()
        return jsonify({'success': True, 'data': teachers})
        
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/admin/courses', methods=['GET'])
@login_required(role='admin')
def admin_courses():
    """Get all courses"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT course_id, course_code, course_name, semester FROM course ORDER BY semester, course_code"
        cursor.execute(query)
        courses = cursor.fetchall()
        return jsonify({'success': True, 'data': courses})
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/admin/student/details', methods=['GET'])
@login_required(role='admin')
def admin_student_details():
    """Get detailed student information including courses, attendance, and results"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        student_id = request.args.get('student_id')
        
        if not student_id:
            return jsonify({'success': False, 'message': 'Student ID required'}), 400
        
        # Get student basic info
        student_query = "SELECT * FROM student WHERE student_id = %s"
        cursor.execute(student_query, (student_id,))
        student = cursor.fetchone()
        
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
        
        # Get current semester courses
        courses_query = """
            SELECT c.course_id, c.course_code, c.course_name, c.credits, c.semester,
                   t.name as teacher_name
            FROM student_course sc
            JOIN course c ON sc.course_id = c.course_id
            LEFT JOIN teacher_course tc ON c.course_id = tc.course_id
            LEFT JOIN teacher t ON tc.teacher_id = t.teacher_id
            WHERE sc.student_id = %s
            ORDER BY c.semester DESC, c.course_code
        """
        cursor.execute(courses_query, (student_id,))
        courses = cursor.fetchall()
        
        # Get attendance by course
        attendance_query = """
            SELECT c.course_id, c.course_code, c.course_name,
                   COUNT(a.attendance_id) as total_classes,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_count,
                   SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_count,
                   CASE 
                       WHEN COUNT(a.attendance_id) > 0 
                       THEN ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.attendance_id)) * 100, 2)
                       ELSE 0 
                   END as attendance_percentage
            FROM student_course sc
            JOIN course c ON sc.course_id = c.course_id
            LEFT JOIN attendance a ON sc.student_id = a.student_id AND sc.course_id = a.course_id
            WHERE sc.student_id = %s
            GROUP BY c.course_id, c.course_code, c.course_name
            ORDER BY c.course_code
        """
        cursor.execute(attendance_query, (student_id,))
        attendance = cursor.fetchall()
        
        # Get results
        results_query = """
            SELECT es.*, c.course_code, c.course_name
            FROM exam_score es
            JOIN course c ON es.course_id = c.course_id
            WHERE es.student_id = %s
            ORDER BY es.semester DESC, es.exam_date DESC
        """
        cursor.execute(results_query, (student_id,))
        results = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'data': {
                'student': student,
                'courses': courses,
                'attendance': attendance,
                'results': results
            }
        })
        
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/admin/teacher/details', methods=['GET'])
@login_required(role='admin')
def admin_teacher_details():
    """Get detailed teacher information including courses and students"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        teacher_id = request.args.get('teacher_id')
        
        if not teacher_id:
            return jsonify({'success': False, 'message': 'Teacher ID required'}), 400
        
        # Get teacher basic info
        teacher_query = "SELECT * FROM teacher WHERE teacher_id = %s"
        cursor.execute(teacher_query, (teacher_id,))
        teacher = cursor.fetchone()
        
        if not teacher:
            return jsonify({'success': False, 'message': 'Teacher not found'}), 404
        
        # Get courses taught
        courses_query = """
            SELECT c.course_id, c.course_code, c.course_name, c.credits, c.semester,
                   COUNT(DISTINCT sc.student_id) as enrolled_students
            FROM teacher_course tc
            JOIN course c ON tc.course_id = c.course_id
            LEFT JOIN student_course sc ON c.course_id = sc.course_id
            WHERE tc.teacher_id = %s
            GROUP BY c.course_id, c.course_code, c.course_name, c.credits, c.semester
            ORDER BY c.semester, c.course_code
        """
        cursor.execute(courses_query, (teacher_id,))
        courses = cursor.fetchall()
        
        # Get students for each course
        students_by_course = {}
        for course in courses:
            students_query = """
                SELECT s.student_id, s.name, s.roll_number, s.email, s.semester
                FROM student_course sc
                JOIN student s ON sc.student_id = s.student_id
                WHERE sc.course_id = %s AND s.is_active = TRUE
                ORDER BY s.roll_number
            """
            cursor.execute(students_query, (course['course_id'],))
            students_by_course[course['course_id']] = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'data': {
                'teacher': teacher,
                'courses': courses,
                'students_by_course': students_by_course
            }
        })
        
    except Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/admin/results', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_results():
    """Get student results"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        semester = request.args.get('semester')
        student_id = request.args.get('student_id')
        
        if student_id:
            query = """
                SELECT es.*, c.course_code, c.course_name, s.name as student_name, s.roll_number
                FROM exam_score es
                JOIN course c ON es.course_id = c.course_id
                JOIN student s ON es.student_id = s.student_id
                WHERE es.student_id = %s
                ORDER BY es.semester DESC, es.exam_date DESC
            """
            cursor.execute(query, (student_id,))
        elif semester:
            query = """
                SELECT es.*, c.course_code, c.course_name, s.name as student_name, s.roll_number
                FROM exam_score es
                JOIN course c ON es.course_id = c.course_id
                JOIN student s ON es.student_id = s.student_id
                WHERE es.semester = %s
                ORDER BY s.roll_number, c.course_code
            """
            cursor.execute(query, (semester,))
        else:
            query = """
                SELECT es.*, c.course_code, c.course_name, s.name as student_name, s.roll_number
                FROM exam_score es
                JOIN course c ON es.course_id = c.course_id
                JOIN student s ON es.student_id = s.student_id
                ORDER BY es.semester DESC, s.roll_number, c.course_code
            """
            cursor.execute(query)
        
        if request.method == 'GET':
            results = cursor.fetchall()
            return jsonify({'success': True, 'data': results})
        
        elif request.method == 'POST':
            data = request.get_json()
            student_id = data.get('student_id')
            course_id = data.get('course_id')
            semester = data.get('semester')
            exam_type = data.get('exam_type')
            score = data.get('score')
            max_score = data.get('max_score', 100)
            exam_date = data.get('exam_date')
            
            if not all([student_id, course_id, semester, exam_type, score, exam_date]):
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
            insert_query = """
                INSERT INTO exam_score (student_id, course_id, semester, exam_type, score, max_score, exam_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (student_id, course_id, semester, exam_type, score, max_score, exam_date))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Result uploaded successfully'})
        
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Serve static files (HTML, CSS, JS) - must be last to avoid conflicts with API routes
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # Don't serve API routes as static files
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)