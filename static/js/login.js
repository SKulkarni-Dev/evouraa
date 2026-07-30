/*=========================================
LOGIN PAGE
=========================================*/

document.addEventListener("DOMContentLoaded", () => {

    const form = document.querySelector("form");

    const password = document.getElementById("password");

    const togglePassword = document.getElementById("togglePassword");


    /*=========================================
    SHOW / HIDE PASSWORD
    =========================================*/

    togglePassword.addEventListener("click", () => {

        if (password.type === "password") {

            password.type = "text";

            togglePassword.classList.remove("fa-eye");
            togglePassword.classList.add("fa-eye-slash");

        }

        else {

            password.type = "password";

            togglePassword.classList.remove("fa-eye-slash");
            togglePassword.classList.add("fa-eye");

        }

    });


    /*=========================================
    BASIC VALIDATION
    =========================================*/

    form.addEventListener("submit", (e) => {

        const emailPhone = document
            .querySelector("input[name='email_or_phone']")
            .value
            .trim();

        if (emailPhone === "") {

            e.preventDefault();

            alert("Please enter your Email or Phone Number.");

            return;

        }

        if (password.value.trim() === "") {

            e.preventDefault();

            alert("Please enter your Password.");

            return;

        }

    });

});