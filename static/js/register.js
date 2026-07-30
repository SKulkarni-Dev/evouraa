/*=========================================
REGISTER PAGE
=========================================*/

document.addEventListener("DOMContentLoaded", () => {

    const form = document.querySelector("form");
    const password = document.querySelector("input[name='password']");
    const confirmPassword = document.querySelector("input[name='confirm_password']");

    form.addEventListener("submit", (e) => {

        if (password.value.length < 8) {
            e.preventDefault();
            alert("Password must contain at least 8 characters.");
            return;
        }

        if (password.value !== confirmPassword.value) {
            e.preventDefault();
            alert("Passwords do not match.");
            return;
        }
    });
});
