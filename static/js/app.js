console.log("Cameron IP UI Loaded");

function loginUser(event) {
    event.preventDefault();

    const user = document.getElementById("username").value.trim();
    const pass = document.getElementById("password").value.trim();

    // TEMPORARY DEV CREDENTIALS
    if (user === "admin" && pass === "password") {
        window.location.href = "dashboard.html";
        return false;
    }

    // Show error
    document.getElementById("login-error").style.display = "block";
    return false;
}
if (user === "admin" && pass === "password") {
    localStorage.setItem("loggedIn", "true");
    window.location.href = "dashboard.html";
    return false;
}
function logout() {
    localStorage.removeItem("loggedIn");
    window.location.href = "login.html";
}