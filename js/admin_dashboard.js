// Check if user is logged in
const user = JSON.parse(sessionStorage.getItem('user') || '{}');
if (!user || user.role !== 'admin') {
    window.location.href = 'index.html';
}

document.getElementById('userName').textContent = user.name || user.username;

let allCourses = [];
let allStudents = [];
let allTeachers = [];

// Show entity type (students/teachers/results)
function showEntityType(type) {
    document.querySelectorAll('.entity-view').forEach(view => {
        view.classList.remove('active');
    });
    document.querySelectorAll('.selection-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(type + 'View').classList.add('active');
    event.target.classList.add('active');
    
    if (type === 'students') {
        loadCoursesForFilter('studentCourseFilter');
        loadStudents();
    } else if (type === 'teachers') {
        loadCoursesForFilter('teacherCourseFilter');
        loadTeachers();
    } else if (type === 'results') {
        loadResults();
    }
}

// Load courses for filter dropdowns
async function loadCoursesForFilter(selectId) {
    try {
        const response = await fetch('/api/admin/courses');
        const data = await response.json();
        
        if (data.success) {
            allCourses = data.data;
            const select = document.getElementById(selectId);
            select.innerHTML = '<option value="">All Courses</option>';
            
            data.data.forEach(course => {
                const option = document.createElement('option');
                option.value = course.course_id;
                option.textContent = `${course.course_code} - ${course.course_name}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading courses:', error);
    }
}

// Load students with sorting and filtering
async function loadStudents() {
    try {
        const response = await fetch('/api/admin/students');
        const data = await response.json();
        
        if (data.success) {
            allStudents = data.data;
            
            // Apply filters
            let filtered = [...data.data];
            const semesterFilter = document.getElementById('studentSemesterFilter').value;
            const courseFilter = document.getElementById('studentCourseFilter').value;
            
            if (semesterFilter) {
                filtered = filtered.filter(s => s.semester == semesterFilter);
            }
            
            if (courseFilter) {
                filtered = filtered.filter(student => {
                    const courseIds = String(student.course_ids || '').split(',').filter(Boolean);
                    return courseIds.includes(String(courseFilter));
                });
            }
            
            // Apply sorting
            const sortBy = document.getElementById('studentSortBy').value;
            filtered.sort((a, b) => {
                if (sortBy === 'name') {
                    return a.name.localeCompare(b.name);
                } else if (sortBy === 'roll_number') {
                    return a.roll_number.localeCompare(b.roll_number);
                } else if (sortBy === 'semester') {
                    return a.semester - b.semester || a.name.localeCompare(b.name);
                } else if (sortBy === 'department') {
                    return (a.department || '').localeCompare(b.department || '') || a.name.localeCompare(b.name);
                }
                return 0;
            });
            
            const studentsList = document.getElementById('studentsList');
            studentsList.innerHTML = '';
            
            if (filtered.length === 0) {
                studentsList.innerHTML = '<p>No students found.</p>';
                return;
            }
            
            let html = '<table><thead><tr><th>Roll Number</th><th>Name</th><th>Email</th><th>Semester</th><th>Department</th><th>Status</th></tr></thead><tbody>';
            filtered.forEach(student => {
                const statusBadge = student.is_active ? 
                    '<span class="status-badge status-present">Active</span>' : 
                    '<span class="status-badge status-absent">Restricted</span>';
                
                html += `<tr class="clickable-row" onclick="showStudentDetails(${student.student_id})">
                    <td>${student.roll_number}</td>
                    <td>${student.name}</td>
                    <td>${student.email || 'N/A'}</td>
                    <td>${student.semester}</td>
                    <td>${student.department}</td>
                    <td>${statusBadge}</td>
                </tr>`;
            });
            html += '</tbody></table>';
            studentsList.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading students:', error);
    }
}

// Show student details (slide-in view)
async function showStudentDetails(studentId) {
    try {
        const response = await fetch(`/api/admin/student/details?student_id=${studentId}`);
        const data = await response.json();
        
        if (data.success) {
            const { student, courses, attendance, results } = data.data;
            const statusBadge = student.is_active ? 
                '<span class="status-badge status-present">Active</span>' : 
                '<span class="status-badge status-absent">Restricted</span>';
            
            // Group courses by semester
            const currentSemester = student.semester;
            const currentSemCourses = courses.filter(c => c.semester == currentSemester);
            const previousSemCourses = courses.filter(c => c.semester < currentSemester);
            
            // Group results by semester
            const resultsBySemester = {};
            results.forEach(result => {
                const sem = result.semester;
                if (!resultsBySemester[sem]) {
                    resultsBySemester[sem] = [];
                }
                resultsBySemester[sem].push(result);
            });
            
            let content = `
                <div class="detail-section">
                    <div class="info-grid">
                        <div class="info-item">
                            <strong>Name</strong>
                            ${student.name}
                        </div>
                        <div class="info-item">
                            <strong>Roll Number</strong>
                            ${student.roll_number}
                        </div>
                        <div class="info-item">
                            <strong>Email</strong>
                            ${student.email || 'N/A'}
                        </div>
                        <div class="info-item">
                            <strong>Semester</strong>
                            ${student.semester}
                        </div>
                        <div class="info-item">
                            <strong>Department</strong>
                            ${student.department}
                        </div>
                        <div class="info-item">
                            <strong>Status</strong>
                            ${statusBadge}
                        </div>
                    </div>
                    <div class="action-buttons">
                        <button onclick="toggleStudentAccess(${student.student_id}, ${student.is_active ? 0 : 1})" 
                                class="btn ${student.is_active ? 'btn-danger' : 'btn-success'}">
                            ${student.is_active ? 'Restrict Access' : 'Activate Access'}
                        </button>
                        <button onclick="deleteStudent(${student.student_id})" class="btn btn-danger">Delete Student</button>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>Current Semester Courses (Semester ${currentSemester})</h3>
                    ${currentSemCourses.length > 0 ? `
                        <table class="table-container">
                            <thead>
                                <tr><th>Course Code</th><th>Course Name</th><th>Credits</th><th>Teacher</th></tr>
                            </thead>
                            <tbody>
                                ${currentSemCourses.map(course => `
                                    <tr>
                                        <td>${course.course_code}</td>
                                        <td>${course.course_name}</td>
                                        <td>${course.credits}</td>
                                        <td>${course.teacher_name || 'N/A'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    ` : '<p>No courses enrolled for current semester.</p>'}
                </div>
                
                <div class="detail-section">
                    <h3>Attendance by Course</h3>
                    ${attendance.length > 0 ? `
                        <table class="table-container">
                            <thead>
                                <tr><th>Course</th><th>Present</th><th>Absent</th><th>Total</th><th>Percentage</th></tr>
                            </thead>
                            <tbody>
                                ${attendance.map(att => {
                                    const percentage = att.attendance_percentage || 0;
                                    const percentageClass = percentage >= 75 ? 'good' : percentage >= 50 ? 'warning' : 'poor';
                                    return `
                                        <tr>
                                            <td>${att.course_code} - ${att.course_name}</td>
                                            <td>${att.present_count || 0}</td>
                                            <td>${att.absent_count || 0}</td>
                                            <td>${att.total_classes || 0}</td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    ` : '<p>No attendance records found.</p>'}
                </div>
                
                <div class="detail-section">
                    <h3>Previous Semester Results</h3>
                    ${Object.keys(resultsBySemester).length > 0 ? 
                        Object.keys(resultsBySemester).sort((a, b) => b - a).map(sem => `
                            <h4 style="margin-top: 15px; color: #667eea;">Semester ${sem}</h4>
                            <table class="table-container">
                                <thead>
                                    <tr><th>Course</th><th>Exam Type</th><th>Score</th><th>Max Score</th><th>Percentage</th><th>Date</th></tr>
                                </thead>
                                <tbody>
                                    ${resultsBySemester[sem].map(result => {
                                        const percentage = ((result.score / result.max_score) * 100).toFixed(1);
                                        return `
                                            <tr>
                                                <td>${result.course_code} - ${result.course_name}</td>
                                                <td>${result.exam_type}</td>
                                                <td>${result.score}</td>
                                                <td>${result.max_score}</td>
                                                <td>${percentage}%</td>
                                                <td>${result.exam_date || 'N/A'}</td>
                                            </tr>
                                        `;
                                    }).join('')}
                                </tbody>
                            </table>
                        `).join('') : '<p>No results found.</p>'}
                </div>
            `;
            
            document.getElementById('detailTitle').textContent = `Student: ${student.name}`;
            document.getElementById('detailContent').innerHTML = content;
            document.getElementById('detailView').classList.add('active');
        }
    } catch (error) {
        console.error('Error loading student details:', error);
        alert('Error loading student details');
    }
}

function closeDetailView() {
    document.getElementById('detailView').classList.remove('active');
}

// Toggle student access
async function toggleStudentAccess(studentId, isActive) {
    try {
        const response = await fetch('/api/admin/students', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'restrict',
                student_id: studentId,
                is_active: isActive
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(isActive ? 'Student access activated' : 'Student access restricted');
            closeDetailView();
            loadStudents();
        } else {
            alert('Failed to update student access');
        }
    } catch (error) {
        console.error('Error updating access:', error);
        alert('Error updating student access');
    }
}

// Delete student
async function deleteStudent(studentId) {
    if (!confirm('Are you sure you want to permanently delete this student from the database?')) return;
    
    try {
        const response = await fetch('/api/admin/students', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'delete',
                student_id: studentId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Student deleted successfully!');
            closeDetailView();
            loadStudents();
        } else {
            alert('Failed to delete student');
        }
    } catch (error) {
        console.error('Error deleting student:', error);
        alert('Error deleting student');
    }
}

// Load teachers with sorting and filtering
async function loadTeachers() {
    try {
        const response = await fetch('/api/admin/teachers');
        const data = await response.json();
        
        if (data.success) {
            allTeachers = data.data;
            
            let filtered = [...data.data];
            const semesterFilter = document.getElementById('teacherSemesterFilter').value;
            const courseFilter = document.getElementById('teacherCourseFilter').value;

            if (semesterFilter) {
                filtered = filtered.filter(teacher => {
                    const semesters = String(teacher.course_semesters || '').split(',').filter(Boolean);
                    return semesters.includes(String(semesterFilter));
                });
            }

            if (courseFilter) {
                filtered = filtered.filter(teacher => {
                    const courseIds = String(teacher.course_ids || '').split(',').filter(Boolean);
                    return courseIds.includes(String(courseFilter));
                });
            }

            const sortBy = document.getElementById('teacherSortBy').value;
            filtered.sort((a, b) => {
                if (sortBy === 'name') {
                    return a.name.localeCompare(b.name);
                }
                if (sortBy === 'semester') {
                    const aSem = Math.min(...String(a.course_semesters || '999').split(',').map(Number));
                    const bSem = Math.min(...String(b.course_semesters || '999').split(',').map(Number));
                    return aSem - bSem || a.name.localeCompare(b.name);
                }
                if (sortBy === 'course') {
                    return (a.courses_taught || '').localeCompare(b.courses_taught || '');
                }
                if (sortBy === 'students') {
                    return (Number(b.student_count) || 0) - (Number(a.student_count) || 0);
                }
                return 0;
            });
            
            const teachersList = document.getElementById('teachersList');
            teachersList.innerHTML = '';
            
            if (filtered.length === 0) {
                teachersList.innerHTML = '<p>No teachers found.</p>';
                return;
            }
            
            let html = '<table><thead><tr><th>Name</th><th>Email</th><th>Department</th><th>Courses Taught</th><th>Course Count</th></tr></thead><tbody>';
            filtered.forEach(teacher => {
                html += `<tr class="clickable-row" onclick="showTeacherDetails(${teacher.teacher_id})">
                    <td>${teacher.name}</td>
                    <td>${teacher.email || 'N/A'}</td>
                    <td>${teacher.department || 'N/A'}</td>
                    <td>${teacher.courses_taught || 'None'}</td>
                    <td>${teacher.course_count || 0}</td>
                </tr>`;
            });
            html += '</tbody></table>';
            teachersList.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading teachers:', error);
    }
}

// Show teacher details (slide-in view)
async function showTeacherDetails(teacherId) {
    try {
        const response = await fetch(`/api/admin/teacher/details?teacher_id=${teacherId}`);
        const data = await response.json();
        
        if (data.success) {
            const { teacher, courses, students_by_course } = data.data;
            
            let content = `
                <div class="detail-section">
                    <div class="info-grid">
                        <div class="info-item">
                            <strong>Name</strong>
                            ${teacher.name}
                        </div>
                        <div class="info-item">
                            <strong>Email</strong>
                            ${teacher.email || 'N/A'}
                        </div>
                        <div class="info-item">
                            <strong>Department</strong>
                            ${teacher.department || 'N/A'}
                        </div>
                        <div class="info-item">
                            <strong>Courses Taught</strong>
                            ${courses.length}
                        </div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>Courses Teaching</h3>
                    ${courses.length > 0 ? `
                        <table class="table-container">
                            <thead>
                                <tr><th>Course Code</th><th>Course Name</th><th>Semester</th><th>Credits</th><th>Enrolled Students</th></tr>
                            </thead>
                            <tbody>
                                ${courses.map(course => `
                                    <tr>
                                        <td>${course.course_code}</td>
                                        <td>${course.course_name}</td>
                                        <td>${course.semester}</td>
                                        <td>${course.credits}</td>
                                        <td>${course.enrolled_students || 0}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    ` : '<p>No courses assigned.</p>'}
                </div>
                
                <div class="detail-section">
                    <h3>Students by Course</h3>
                    ${courses.length > 0 ? courses.map(course => {
                        const students = students_by_course[course.course_id] || [];
                        return `
                            <div style="margin-bottom: 30px;">
                                <h4 style="color: #667eea; margin-bottom: 10px;">${course.course_code} - ${course.course_name}</h4>
                                ${students.length > 0 ? `
                                    <table class="table-container">
                                        <thead>
                                            <tr><th>Roll Number</th><th>Name</th><th>Email</th><th>Semester</th></tr>
                                        </thead>
                                        <tbody>
                                            ${students.map(student => `
                                                <tr>
                                                    <td>${student.roll_number}</td>
                                                    <td>${student.name}</td>
                                                    <td>${student.email || 'N/A'}</td>
                                                    <td>${student.semester}</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                ` : '<p>No students enrolled in this course.</p>'}
                            </div>
                        `;
                    }).join('') : '<p>No courses assigned.</p>'}
                </div>
            `;
            
            document.getElementById('detailTitle').textContent = `Teacher: ${teacher.name}`;
            document.getElementById('detailContent').innerHTML = content;
            document.getElementById('detailView').classList.add('active');
        }
    } catch (error) {
        console.error('Error loading teacher details:', error);
        alert('Error loading teacher details');
    }
}

// Load results
async function loadResults() {
    const semester = document.getElementById('resultsSemesterFilter').value;
    const url = semester ? `/api/admin/results?semester=${semester}` : '/api/admin/results';
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            const resultsList = document.getElementById('resultsList');
            resultsList.innerHTML = '';
            
            if (data.data.length === 0) {
                resultsList.innerHTML = '<p>No results found.</p>';
                return;
            }
            
            let html = '<table><thead><tr><th>Roll Number</th><th>Student Name</th><th>Course</th><th>Exam Type</th><th>Score</th><th>Max Score</th><th>Percentage</th><th>Date</th><th>Semester</th></tr></thead><tbody>';
            data.data.forEach(result => {
                const percentage = ((result.score / result.max_score) * 100).toFixed(1);
                html += `<tr>
                    <td>${result.roll_number}</td>
                    <td>${result.student_name}</td>
                    <td>${result.course_code} - ${result.course_name}</td>
                    <td>${result.exam_type || 'N/A'}</td>
                    <td>${result.score}</td>
                    <td>${result.max_score}</td>
                    <td>${percentage}%</td>
                    <td>${result.exam_date || 'N/A'}</td>
                    <td>${result.semester}</td>
                </tr>`;
            });
            html += '</tbody></table>';
            resultsList.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading results:', error);
    }
}

// Show add student modal
function showAddStudentModal() {
    document.getElementById('studentModal').style.display = 'block';
}

function closeStudentModal() {
    document.getElementById('studentModal').style.display = 'none';
    document.getElementById('studentForm').reset();
}

// Handle student form
document.getElementById('studentForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        action: 'add',
        username: document.getElementById('studentUsername').value,
        password: document.getElementById('studentPassword').value,
        name: document.getElementById('studentName').value,
        email: document.getElementById('studentEmail').value,
        roll_number: document.getElementById('studentRollNumber').value,
        semester: parseInt(document.getElementById('studentSemester').value),
        department: document.getElementById('studentDepartment').value
    };
    
    try {
        const response = await fetch('/api/admin/students', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Student added successfully!');
            closeStudentModal();
            loadStudents();
        } else {
            alert('Failed to add student: ' + result.message);
        }
    } catch (error) {
        console.error('Error adding student:', error);
        alert('Error adding student');
    }
});

// Logout
function logout() {
    fetch('/api/logout').then(() => {
        sessionStorage.clear();
        window.location.href = 'index.html';
    });
}

// Show upload results modal
async function showUploadResultsModal() {
    // Load students
    try {
        const response = await fetch('/api/admin/students');
        const data = await response.json();
        const select = document.getElementById('resultStudentId');
        select.innerHTML = '<option value="">Select Student</option>';
        if (data.success) {
            data.data.forEach(student => {
                const option = document.createElement('option');
                option.value = student.student_id;
                option.textContent = `${student.roll_number} - ${student.name}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading students:', error);
    }
    
    // Load courses
    try {
        const response = await fetch('/api/admin/courses');
        const data = await response.json();
        const select = document.getElementById('resultCourseId');
        select.innerHTML = '<option value="">Select Course</option>';
        if (data.success) {
            data.data.forEach(course => {
                const option = document.createElement('option');
                option.value = course.course_id;
                option.textContent = `${course.course_code} - ${course.course_name}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading courses:', error);
    }
    
    document.getElementById('uploadResultsModal').style.display = 'block';
}

function closeUploadResultsModal() {
    document.getElementById('uploadResultsModal').style.display = 'none';
    document.getElementById('uploadResultsForm').reset();
}

// Handle upload results form
document.getElementById('uploadResultsForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        student_id: parseInt(document.getElementById('resultStudentId').value),
        course_id: parseInt(document.getElementById('resultCourseId').value),
        semester: parseInt(document.getElementById('resultSemester').value),
        exam_type: document.getElementById('resultExamType').value,
        score: parseFloat(document.getElementById('resultScore').value),
        max_score: parseFloat(document.getElementById('resultMaxScore').value),
        exam_date: document.getElementById('resultExamDate').value
    };
    
    try {
        const response = await fetch('/api/admin/results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Result uploaded successfully!');
            closeUploadResultsModal();
            loadResults();
        } else {
            alert('Failed to upload result: ' + result.message);
        }
    } catch (error) {
        console.error('Error uploading result:', error);
        alert('Error uploading result');
    }
});

// Close modals when clicking outside
window.onclick = function(event) {
    const studentModal = document.getElementById('studentModal');
    const uploadResultsModal = document.getElementById('uploadResultsModal');
    if (event.target === studentModal) {
        closeStudentModal();
    }
    if (event.target === uploadResultsModal) {
        closeUploadResultsModal();
    }
}

// Load initial data
loadCoursesForFilter('studentCourseFilter');
loadStudents();
