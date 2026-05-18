// Check if user is logged in
const user = JSON.parse(sessionStorage.getItem('user') || '{}');
if (!user || user.role !== 'teacher') {
    window.location.href = 'index.html';
}

document.getElementById('userName').textContent = user.name || user.username;

let attendanceData = {};
let selectedCourseId = null;
let selectedSection = null;
let coursesData = [];

// Load courses as selectable cards
async function loadCourses() {
    try {
        const response = await fetch('/api/teacher/courses');
        const data = await response.json();
        
        if (data.success) {
            coursesData = data.data;
            const coursesList = document.getElementById('coursesList');
            coursesList.innerHTML = '';
            
            data.data.forEach(course => {
                const card = document.createElement('div');
                card.className = 'course-card-selectable';
                card.dataset.courseId = course.course_id;
                card.innerHTML = `
                    <h3>${course.course_code}</h3>
                    <p><strong>${course.course_name}</strong></p>
                    <p>Credits: ${course.credits}</p>
                    <p>Semester: ${course.semester}</p>
                    <p>Enrolled Students: ${course.enrolled_students || 0}</p>
                `;
                card.onclick = () => selectCourse(course.course_id);
                coursesList.appendChild(card);
            });
        }
    } catch (error) {
        console.error('Error loading courses:', error);
    }
}

// Select a course
function selectCourse(courseId) {
    selectedCourseId = courseId;
    
    // Update active course card
    document.querySelectorAll('.course-card-selectable').forEach(card => {
        card.classList.remove('active');
        if (card.dataset.courseId == courseId) {
            card.classList.add('active');
        }
    });
    
    // Hide no course selected message
    document.getElementById('noCourseSelected').style.display = 'none';
    
    // Show current section or default to attendance
    if (selectedSection) {
        showSection(selectedSection);
    } else {
        showSection('attendance');
    }
}

// Show a section in the sidebar
function showSection(sectionName) {
    if (!selectedCourseId) {
        alert('Please select a course first');
        return;
    }
    
    selectedSection = sectionName;
    
    // Update sidebar active state
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.section === sectionName) {
            item.classList.add('active');
        }
    });
    
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
        section.style.display = 'none';
    });
    
    // Hide no course selected message
    document.getElementById('noCourseSelected').style.display = 'none';
    
    // Show selected section
    const sectionMap = {
        'attendance': 'attendanceSection',
        'attendanceStats': 'attendanceStatsSection',
        'assignments': 'assignmentsSection',
        'students': 'studentsSection'
    };
    
    const sectionId = sectionMap[sectionName];
    if (sectionId) {
        const section = document.getElementById(sectionId);
        section.style.display = 'block';
        section.classList.add('active');
        
        // Load section-specific data
        if (sectionName === 'attendance') {
            loadAttendanceStudents();
        } else if (sectionName === 'attendanceStats') {
            loadAttendanceStats();
        } else if (sectionName === 'assignments') {
            loadAssignments();
        } else if (sectionName === 'students') {
            loadCourseStudents();
        }
    }
}

// Load students for attendance
async function loadAttendanceStudents() {
    if (!selectedCourseId) return;
    
    const date = document.getElementById('attendanceDate').value || new Date().toISOString().split('T')[0];
    document.getElementById('attendanceDate').value = date;
    
    try {
        const response = await fetch(`/api/teacher/attendance?course_id=${selectedCourseId}&date=${date}`);
        const data = await response.json();
        
        if (data.success) {
            const list = document.getElementById('attendanceStudentsList');
            list.innerHTML = '';
            
            if (data.data.length === 0) {
                list.innerHTML = '<p>No students enrolled in this course.</p>';
                return;
            }
            
            let html = '<table><thead><tr><th>Roll Number</th><th>Name</th><th>Attendance</th></tr></thead><tbody>';
            attendanceData = {};
            
            data.data.forEach(student => {
                attendanceData[student.student_id] = student.attendance_status || 'Present';
                const checked = student.attendance_status === 'Present' ? 'checked' : '';
                html += `<tr>
                    <td>${student.roll_number}</td>
                    <td>${student.name}</td>
                    <td>
                        <label>
                            <input type="checkbox" class="attendance-checkbox" 
                                   ${checked} 
                                   onchange="updateAttendance(${student.student_id}, this.checked)">
                            Present
                        </label>
                    </td>
                </tr>`;
            });
            html += '</tbody></table>';
            list.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading students:', error);
    }
}

// Update attendance in memory
function updateAttendance(studentId, isPresent) {
    attendanceData[studentId] = isPresent ? 'Present' : 'Absent';
}

// Save attendance
async function saveAttendance() {
    if (!selectedCourseId) {
        alert('Please select a course');
        return;
    }
    
    const date = document.getElementById('attendanceDate').value;
    
    if (!date) {
        alert('Please select a date');
        return;
    }
    
    const promises = Object.keys(attendanceData).map(studentId => {
        return fetch('/api/teacher/attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                student_id: parseInt(studentId),
                course_id: parseInt(selectedCourseId),
                date: date,
                status: attendanceData[studentId]
            })
        });
    });
    
    try {
        await Promise.all(promises);
        alert('Attendance saved successfully!');
        loadAttendanceStudents();
    } catch (error) {
        console.error('Error saving attendance:', error);
        alert('Error saving attendance');
    }
}

// Load assignments
async function loadAssignments() {
    if (!selectedCourseId) return;
    
    try {
        const response = await fetch(`/api/teacher/assignments?course_id=${selectedCourseId}`);
        const data = await response.json();
        
        if (data.success) {
            const assignmentsList = document.getElementById('assignmentsList');
            assignmentsList.innerHTML = '';
            
            if (data.data.length === 0) {
                assignmentsList.innerHTML = '<p>No assignments created for this course.</p>';
                return;
            }
            
            data.data.forEach(assignment => {
                const card = document.createElement('div');
                card.className = 'card';
                const dueDate = assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : 'No due date';
                
                card.innerHTML = `
                    <h3>${assignment.title}</h3>
                    <p><strong>Course:</strong> ${assignment.course_code} - ${assignment.course_name}</p>
                    <p>${assignment.description || 'No description'}</p>
                    <p><strong>Due Date:</strong> ${dueDate}</p>
                    <div class="action-buttons" style="margin-top: 10px;">
                        <button onclick="deleteAssignment(${assignment.assignment_id})" class="btn btn-danger">Delete</button>
                    </div>
                `;
                assignmentsList.appendChild(card);
            });
        }
    } catch (error) {
        console.error('Error loading assignments:', error);
    }
}

// Delete assignment
async function deleteAssignment(assignmentId) {
    if (!confirm('Are you sure you want to delete this assignment?')) return;
    
    try {
        const response = await fetch(`/api/teacher/assignments?assignment_id=${assignmentId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Assignment deleted successfully!');
            loadAssignments();
        } else {
            alert('Failed to delete assignment');
        }
    } catch (error) {
        console.error('Error deleting assignment:', error);
        alert('Error deleting assignment');
    }
}

// Show add assignment modal
async function showAddAssignmentModal() {
    if (!selectedCourseId) {
        alert('Please select a course first');
        return;
    }
    
    // Set the course in the modal
    const select = document.getElementById('assignmentCourse');
    select.innerHTML = '<option value="">Select Course</option>';
    
    coursesData.forEach(course => {
        const option = document.createElement('option');
        option.value = course.course_id;
        option.textContent = `${course.course_code} - ${course.course_name}`;
        if (course.course_id == selectedCourseId) {
            option.selected = true;
        }
        select.appendChild(option);
    });
    
    document.getElementById('assignmentModal').style.display = 'block';
}

function closeAssignmentModal() {
    document.getElementById('assignmentModal').style.display = 'none';
    document.getElementById('assignmentForm').reset();
}

// Handle assignment form
document.getElementById('assignmentForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        course_id: document.getElementById('assignmentCourse').value || selectedCourseId,
        title: document.getElementById('assignmentTitle').value,
        description: document.getElementById('assignmentDescription').value,
        due_date: document.getElementById('assignmentDueDate').value
    };
    
    try {
        const response = await fetch('/api/teacher/assignments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Assignment created successfully!');
            closeAssignmentModal();
            loadAssignments();
        } else {
            alert('Failed to create assignment: ' + result.message);
        }
    } catch (error) {
        console.error('Error creating assignment:', error);
        alert('Error creating assignment');
    }
});

// Load attendance statistics
async function loadAttendanceStats() {
    if (!selectedCourseId) return;
    
    const sortOrder = document.getElementById('sortOrderSelect').value;
    const minPercentage = document.getElementById('minPercentage').value;
    const maxPercentage = document.getElementById('maxPercentage').value;
    
    try {
        let url = `/api/teacher/attendance/stats?course_id=${selectedCourseId}&sort_order=${sortOrder}`;
        if (minPercentage) {
            url += `&min_percentage=${minPercentage}`;
        }
        if (maxPercentage) {
            url += `&max_percentage=${maxPercentage}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            const list = document.getElementById('attendanceStatsList');
            list.innerHTML = '';
            
            if (data.data.length === 0) {
                list.innerHTML = '<p>No students found matching the criteria.</p>';
                return;
            }
            
            let html = '<table><thead><tr><th>Roll Number</th><th>Name</th><th>Present</th><th>Absent</th><th>Total Classes</th><th>Attendance %</th></tr></thead><tbody>';
            
            data.data.forEach(student => {
                const percentage = student.attendance_percentage || 0;
                const percentageClass = percentage >= 75 ? 'good' : percentage >= 50 ? 'warning' : 'poor';
                html += `<tr>
                    <td>${student.roll_number}</td>
                    <td>${student.name}</td>
                    <td>${student.present_count || 0}</td>
                    <td>${student.absent_count || 0}</td>
                    <td>${student.total_classes || 0}</td>
                    <td class="${percentageClass}">${percentage.toFixed(2)}%</td>
                </tr>`;
            });
            html += '</tbody></table>';
            list.innerHTML = html;
        } else {
            document.getElementById('attendanceStatsList').innerHTML = `<p>Error: ${data.message}</p>`;
        }
    } catch (error) {
        console.error('Error loading attendance statistics:', error);
        document.getElementById('attendanceStatsList').innerHTML = '<p>Error loading attendance statistics.</p>';
    }
}

// Clear statistics filters
function clearStatsFilters() {
    document.getElementById('minPercentage').value = '';
    document.getElementById('maxPercentage').value = '';
    loadAttendanceStats();
}

// Load students in course
async function loadCourseStudents() {
    if (!selectedCourseId) return;
    
    try {
        const response = await fetch(`/api/teacher/students?course_id=${selectedCourseId}`);
        const data = await response.json();
        
        if (data.success) {
            const list = document.getElementById('studentsList');
            list.innerHTML = '';
            
            if (data.data.length === 0) {
                list.innerHTML = '<p>No students enrolled in this course.</p>';
                return;
            }
            
            let html = '<table><thead><tr><th>Roll Number</th><th>Name</th><th>Email</th><th>Semester</th><th>Actions</th></tr></thead><tbody>';
            data.data.forEach(student => {
                html += `<tr>
                    <td>${student.roll_number}</td>
                    <td>${student.name}</td>
                    <td>${student.email || 'N/A'}</td>
                    <td>${student.semester}</td>
                    <td>
                        <button onclick="removeStudentFromCourse(${student.student_id}, ${selectedCourseId})" class="btn btn-danger">Remove</button>
                    </td>
                </tr>`;
            });
            html += '</tbody></table>';
            list.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading students:', error);
    }
}

// Remove student from course
async function removeStudentFromCourse(studentId, courseId) {
    if (!confirm('Are you sure you want to remove this student from the course?')) return;
    
    try {
        const response = await fetch('/api/teacher/students', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'remove',
                student_id: studentId,
                course_id: courseId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Student removed from course successfully!');
            loadCourseStudents();
        } else {
            alert('Failed to remove student');
        }
    } catch (error) {
        console.error('Error removing student:', error);
        alert('Error removing student');
    }
}

// Logout
function logout() {
    fetch('/api/logout').then(() => {
        sessionStorage.clear();
        window.location.href = 'index.html';
    });
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('assignmentModal');
    if (event.target === modal) {
        closeAssignmentModal();
    }
}

// Load initial data
loadCourses();
