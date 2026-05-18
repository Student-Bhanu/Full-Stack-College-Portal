// Check if user is logged in
const user = JSON.parse(sessionStorage.getItem('user') || '{}');
if (!user || user.role !== 'student') {
    window.location.href = 'index.html';
}

document.getElementById('userName').textContent = user.name || user.username;

let selectedCourseId = null;
let selectedSection = null;
let currentSemester = null;
let allCourses = [];

// Show main tab (This Sem or Results)
function showMainTab(tabName) {
    document.querySelectorAll('.main-tab-content').forEach(tab => {
        tab.classList.remove('active');
        tab.style.display = 'none';
    });
    document.querySelectorAll('.top-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(tabName + 'Tab').classList.add('active');
    document.getElementById(tabName + 'Tab').style.display = 'block';
    event.target.classList.add('active');
    
    if (tabName === 'thisSem') {
        loadCurrentSemesterCourses();
    } else if (tabName === 'results') {
        loadResults();
    }
}

// Load current semester courses
async function loadCurrentSemesterCourses() {
    try {
        const response = await fetch('/api/student/courses');
        const data = await response.json();
        
        if (data.success) {
            allCourses = data.data;
            
            // Determine current semester from courses (most common semester)
            const semesterCounts = {};
            data.data.forEach(course => {
                semesterCounts[course.semester] = (semesterCounts[course.semester] || 0) + 1;
            });
            currentSemester = Object.keys(semesterCounts).reduce((a, b) => 
                semesterCounts[a] > semesterCounts[b] ? a : b
            );
            
            // Filter courses for current semester
            const currentSemCourses = data.data.filter(course => course.semester == currentSemester);
            
            const coursesList = document.getElementById('currentSemCoursesList');
            coursesList.innerHTML = '';
            
            if (currentSemCourses.length === 0) {
                coursesList.innerHTML = '<p>No courses enrolled for this semester.</p>';
                return;
            }
            
            currentSemCourses.forEach(course => {
                const card = document.createElement('div');
                card.className = 'course-card-selectable';
                card.dataset.courseId = course.course_id;
                card.innerHTML = `
                    <h3>${course.course_code}</h3>
                    <p><strong>${course.course_name}</strong></p>
                    <p>Credits: ${course.credits}</p>
                    ${course.teacher_name ? `<p>Teacher: ${course.teacher_name}</p>` : ''}
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
        'assignments': 'assignmentsSection'
    };
    
    const sectionId = sectionMap[sectionName];
    if (sectionId) {
        const section = document.getElementById(sectionId);
        section.style.display = 'block';
        section.classList.add('active');
        
        // Load section-specific data
        if (sectionName === 'attendance') {
            loadAttendance();
        } else if (sectionName === 'assignments') {
            loadAssignments();
        }
    }
}

// Load attendance for selected course
async function loadAttendance() {
    if (!selectedCourseId) return;
    
    try {
        const response = await fetch(`/api/student/attendance?course_id=${selectedCourseId}`);
        const data = await response.json();
        
        if (data.success) {
            const attendanceList = document.getElementById('attendanceList');
            attendanceList.innerHTML = '';
            
            if (data.data.length === 0) {
                attendanceList.innerHTML = '<p>No attendance records found.</p>';
                return;
            }
            
            // Calculate summary
            let presentCount = 0;
            let totalCount = data.data.length;
            data.data.forEach(record => {
                if (record.status === 'Present') presentCount++;
            });
            const percentage = totalCount > 0 ? ((presentCount / totalCount) * 100).toFixed(1) : 0;
            
            let html = `<div style="margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <h3>Attendance Summary</h3>
                <p><strong>Present:</strong> ${presentCount} / <strong>Total:</strong> ${totalCount} (<strong>${percentage}%</strong>)</p>
            </div>`;
            
            html += '<table><thead><tr><th>Date</th><th>Status</th></tr></thead><tbody>';
            data.data.forEach(record => {
                const statusClass = record.status === 'Present' ? 'status-present' : 'status-absent';
                html += `<tr>
                    <td>${record.attendance_date}</td>
                    <td><span class="status-badge ${statusClass}">${record.status}</span></td>
                </tr>`;
            });
            html += '</tbody></table>';
            attendanceList.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading attendance:', error);
    }
}

// Load assignments for selected course
async function loadAssignments() {
    if (!selectedCourseId) return;
    
    try {
        const response = await fetch('/api/student/assignments');
        const data = await response.json();
        
        if (data.success) {
            // Filter assignments for selected course
            const courseAssignments = data.data.filter(assignment => 
                assignment.course_id == selectedCourseId
            );
            
            const assignmentsList = document.getElementById('assignmentsList');
            assignmentsList.innerHTML = '';
            
            if (courseAssignments.length === 0) {
                assignmentsList.innerHTML = '<p>No assignments found for this course.</p>';
                return;
            }
            
            courseAssignments.forEach(assignment => {
                const card = document.createElement('div');
                card.className = 'card';
                const statusClass = assignment.submission_status === 'Submitted' ? 'status-submitted' : 'status-pending';
                const dueDate = assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : 'No due date';
                const isOverdue = assignment.due_date && new Date(assignment.due_date) < new Date() && assignment.submission_status === 'Pending';
                
                card.innerHTML = `
                    <h3>${assignment.title}</h3>
                    <p><strong>Course:</strong> ${assignment.course_code} - ${assignment.course_name}</p>
                    <p>${assignment.description || 'No description'}</p>
                    <p><strong>Due Date:</strong> ${dueDate} ${isOverdue ? '<span style="color: red;">(Overdue)</span>' : ''}</p>
                    <p><strong>Status:</strong> <span class="status-badge ${statusClass}">${assignment.submission_status}</span></p>
                    ${assignment.submission_status === 'Pending' ? 
                        `<button onclick="openUploadModal(${assignment.assignment_id})" class="btn btn-primary" style="margin-top: 10px;">Upload Assignment</button>` :
                        `<p style="color: green; margin-top: 10px;">Submitted on: ${new Date(assignment.submitted_at).toLocaleString()}</p>`
                    }
                `;
                assignmentsList.appendChild(card);
            });
        }
    } catch (error) {
        console.error('Error loading assignments:', error);
    }
}

// Load results (previous semesters)
async function loadResults() {
    const semester = document.getElementById('resultsSemesterFilter').value;
    const url = semester ? `/api/student/scores?semester=${semester}` : '/api/student/scores';
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            const resultsList = document.getElementById('resultsList');
            resultsList.innerHTML = '';
            
            if (data.data.length === 0) {
                resultsList.innerHTML = '<p>No exam scores found.</p>';
                return;
            }
            
            // Group by semester
            const groupedBySemester = {};
            data.data.forEach(score => {
                const sem = score.semester;
                if (!groupedBySemester[sem]) {
                    groupedBySemester[sem] = [];
                }
                groupedBySemester[sem].push(score);
            });
            
            let html = '';
            Object.keys(groupedBySemester).sort((a, b) => b - a).forEach(sem => {
                html += `<h3 style="margin-top: 20px; color: #667eea;">Semester ${sem}</h3>`;
                html += '<table><thead><tr><th>Course</th><th>Exam Type</th><th>Score</th><th>Max Score</th><th>Percentage</th><th>Date</th></tr></thead><tbody>';
                groupedBySemester[sem].forEach(score => {
                    const percentage = ((score.score / score.max_score) * 100).toFixed(1);
                    html += `<tr>
                        <td>${score.course_code} - ${score.course_name}</td>
                        <td>${score.exam_type || 'N/A'}</td>
                        <td>${score.score}</td>
                        <td>${score.max_score}</td>
                        <td>${percentage}%</td>
                        <td>${score.exam_date || 'N/A'}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
            });
            
            resultsList.innerHTML = html;
        }
    } catch (error) {
        console.error('Error loading scores:', error);
    }
}

// Upload modal
function openUploadModal(assignmentId) {
    document.getElementById('uploadAssignmentId').value = assignmentId;
    document.getElementById('uploadModal').style.display = 'block';
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
    document.getElementById('uploadForm').reset();
}

// Handle upload form
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const assignmentId = document.getElementById('uploadAssignmentId').value;
    const fileInput = document.getElementById('assignmentFile');
    
    // For demo purposes, we'll just use the filename
    // In a real app, you'd upload the file to the server
    const fileName = fileInput.files[0] ? fileInput.files[0].name : 'assignment.pdf';
    
    try {
        const response = await fetch('/api/student/assignments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                assignment_id: assignmentId,
                file_path: fileName
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Assignment uploaded successfully!');
            closeUploadModal();
            loadAssignments();
        } else {
            alert('Failed to upload assignment: ' + data.message);
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('Error uploading assignment');
    }
});

// Logout
function logout() {
    fetch('/api/logout').then(() => {
        sessionStorage.clear();
        window.location.href = 'index.html';
    });
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('uploadModal');
    if (event.target === modal) {
        closeUploadModal();
    }
}

// Load initial data
loadCurrentSemesterCourses();
