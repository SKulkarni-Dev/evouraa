from datetime import datetime

from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from database.database import db
from database.models import User
from utils.otp_utils import generate_otp, verify_otp, generate_reset_token, consume_reset_token
from utils.mailer import send_otp_email, send_password_reset_email

auth = Blueprint("auth", __name__)

PENDING_SESSION_KEY = "pending_registration_user_id"


# ==========================================
# REGISTER
# Creates the account as unverified, emails a 6-digit OTP,
# and sends the user to /verify-otp instead of logging them
# straight in.
# ==========================================

@auth.route("/register", methods=["POST"])
def register():

    fullname = request.form.get("fullname")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if not all([fullname, email, phone, password, confirm_password]):
        flash("Please fill all fields.", "danger")
        return redirect(url_for("register_page"))

    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("register_page"))

    existing = User.query.filter_by(email=email).first()

    if existing and existing.is_verified:
        flash("Email already registered.", "warning")
        return redirect(url_for("register_page"))

    if User.query.filter_by(phone=phone).filter(User.email != email).first():
        flash("Phone number already registered.", "warning")
        return redirect(url_for("register_page"))

    hashed_password = generate_password_hash(password)

    if existing and not existing.is_verified:
        # They started registering earlier but never verified -- update
        # their details and resend a fresh OTP instead of blocking them.
        existing.fullname = fullname
        existing.phone = phone
        existing.password_hash = hashed_password
        user = existing
    else:
        user = User(
            fullname=fullname,
            email=email,
            phone=phone,
            password_hash=hashed_password,
            is_verified=False
        )
        db.session.add(user)

    db.session.commit()

    otp_code = generate_otp(identifier=user.email, purpose="register")
    send_otp_email(user.email, user.fullname, otp_code)

    session[PENDING_SESSION_KEY] = user.id

    flash("We've emailed you a 6-digit code. Enter it below to activate your account.", "success")
    return redirect(url_for("auth.verify_otp_page"))


# ==========================================
# EMAIL OTP VERIFICATION
# ==========================================

@auth.route("/verify-otp", methods=["GET"])
def verify_otp_page():

    user_id = session.get(PENDING_SESSION_KEY)
    user = User.query.get(user_id) if user_id else None

    if not user or user.is_verified:
        return redirect(url_for("register_page"))

    return render_template("verify_otp.html", email=user.email)


@auth.route("/verify-otp", methods=["POST"])
def verify_otp_submit():

    user_id = session.get(PENDING_SESSION_KEY)
    user = User.query.get(user_id) if user_id else None

    if not user:
        flash("Your registration session expired. Please register again.", "warning")
        return redirect(url_for("register_page"))

    code = (request.form.get("otp") or "").strip()

    ok, message = verify_otp(identifier=user.email, purpose="register", code=code)

    if not ok:
        flash(message, "danger")
        return redirect(url_for("auth.verify_otp_page"))

    user.is_verified = True
    db.session.commit()

    session.pop(PENDING_SESSION_KEY, None)
    session["user_id"] = user.id
    session["user_name"] = user.fullname

    flash("Welcome to Loop & Love \u2764\ufe0f", "success")
    return redirect(url_for("home"))


@auth.route("/verify-otp/resend", methods=["POST"])
def resend_otp():

    user_id = session.get(PENDING_SESSION_KEY)
    user = User.query.get(user_id) if user_id else None

    if not user:
        flash("Your registration session expired. Please register again.", "warning")
        return redirect(url_for("register_page"))

    otp_code = generate_otp(identifier=user.email, purpose="register")
    send_otp_email(user.email, user.fullname, otp_code)

    flash("A new code has been sent to your email.", "success")
    return redirect(url_for("auth.verify_otp_page"))


# ==========================================
# LOGIN
# ==========================================

@auth.route("/login", methods=["POST"])
def login():

    email_or_phone = request.form.get("email_or_phone")
    password = request.form.get("password")

    user = User.query.filter(
        (User.email == email_or_phone) |
        (User.phone == email_or_phone)
    ).first()

    if user is None:
        flash("Account not found.", "danger")
        return redirect(url_for("login_page"))

    if not check_password_hash(user.password_hash, password):
        flash("Incorrect password.", "danger")
        return redirect(url_for("login_page"))

    if not user.is_verified:
        otp_code = generate_otp(identifier=user.email, purpose="register")
        send_otp_email(user.email, user.fullname, otp_code)
        session[PENDING_SESSION_KEY] = user.id
        flash("Please verify your email first -- we've sent you a new code.", "warning")
        return redirect(url_for("auth.verify_otp_page"))

    session["user_id"] = user.id
    session["user_name"] = user.fullname

    flash("Login Successful.", "success")

    return redirect(url_for("home"))


# ==========================================
# LOGOUT
# ==========================================

@auth.route("/logout")
def logout():

    session.pop("user_id", None)
    session.pop("user_name", None)

    flash("Logged Out Successfully.", "success")

    return redirect(url_for("login_page"))


# ==========================================
# FORGOT PASSWORD
# ==========================================

@auth.route("/forgot-password", methods=["GET"])
def forgot_password_page():
    return render_template("forgot_password.html")


@auth.route("/forgot-password", methods=["POST"])
def forgot_password_submit():

    email = (request.form.get("email") or "").strip()
    user = User.query.filter_by(email=email).first()

    # Same message either way, so we don't reveal which emails have accounts.
    generic_message = "If that email is registered, a reset link is on its way."

    if user:
        token = generate_reset_token(user.id)
        reset_url = url_for("auth.reset_password_page", token=token, _external=True)
        send_password_reset_email(user.email, user.fullname, reset_url)

    flash(generic_message, "success")
    return redirect(url_for("login_page"))


@auth.route("/reset-password/<token>", methods=["GET"])
def reset_password_page(token):

    reset = consume_reset_token(token)

    if not reset:
        flash("This reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password_page"))

    return render_template("reset_password.html", token=token)


@auth.route("/reset-password/<token>", methods=["POST"])
def reset_password_submit(token):

    reset = consume_reset_token(token)

    if not reset:
        flash("This reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password_page"))

    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if not password or password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("auth.reset_password_page", token=token))

    user = reset.user
    user.password_hash = generate_password_hash(password)
    reset.is_used = True
    db.session.commit()

    flash("Password updated. Please log in.", "success")
    return redirect(url_for("login_page"))
