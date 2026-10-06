// Get selected role from sessionStorage
const selectedRole = sessionStorage.getItem('selectedRole') || 'student';

// Update role badge
document.getElementById('roleBadge').textContent = selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1);

// Handle login form submission
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password,
                role: selectedRole
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Store user info in sessionStorage
            sessionStorage.setItem('user', JSON.stringify(data.user));
            sessionStorage.removeItem('selectedRole');
            
            // Redirect based on role
            if (selectedRole === 'student') {
                window.location.href = 'student_dashboard.html';
            } else if (selectedRole === 'teacher') {
                window.location.href = 'teacher_dashboard.html';
            } else if (selectedRole === 'admin') {
                window.location.href = 'admin_dashboard.html';
            }
        } else {
            errorMessage.textContent = data.message || 'Login failed';
            errorMessage.style.display = 'block';
        }
    } catch (error) {
        errorMessage.textContent = 'Error connecting to server';
        errorMessage.style.display = 'block';
        console.error('Login error:', error);
    }
});

