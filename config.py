import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "492336f58e748eef2a923e2a0f2a632061393b2a88f9243ee1154b4c833fc1c8"
    )

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "crochet.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==========================================
    # RAZORPAY (payment gateway)
    # Get test keys from https://dashboard.razorpay.com/app/keys
    # ==========================================

    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")

    # ==========================================
    # OUTBOUND EMAIL (order emails + OTP + password reset)
    # Fill these in your .env file. Until then, emails are
    # logged to the console instead of actually being sent
    # (see utils/mailer.py).
    # ==========================================

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = _bool(os.environ.get("MAIL_USE_TLS"), True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "Loop & Love <no-reply@loopandlove.example>")

    # Where "new order" notifications go
    ADMIN_NOTIFY_EMAIL = os.environ.get("ADMIN_NOTIFY_EMAIL", "owner@loopandlove.example")

    # Emails are only actually sent (vs. printed to console) once
    # MAIL_USERNAME/MAIL_PASSWORD are filled in, unless this is forced on.
    MAIL_SUPPRESS_SEND = not _bool(os.environ.get("MAIL_ENABLED"), False)

    # ==========================================
    # ADMIN PANEL (separate hardcoded login, not tied to the
    # shopper "users" table)
    # ==========================================

    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me-now")

    # ==========================================
    # MISC
    # ==========================================

    STORE_NAME = "Loop & Love"
    ORDER_PREFIX = "VYSH"