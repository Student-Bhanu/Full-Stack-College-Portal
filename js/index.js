// Store selected role in sessionStorage
function selectRole(role) {
    sessionStorage.setItem('selectedRole', role);
    window.location.href = 'login.html';
}

