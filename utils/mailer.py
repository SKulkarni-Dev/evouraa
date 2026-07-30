"""
Thin wrapper around Flask-Mail.

Until MAIL_USERNAME/MAIL_PASSWORD are filled in (see .env.example),
Config.MAIL_SUPPRESS_SEND is True, so Flask-Mail is configured but
never actually opens an SMTP connection — every "send" is printed
to the console instead. This means the rest of the app (OTP flow,
order emails, etc.) can be built and demoed today, and starts
sending real email the moment credentials are added to .env.
"""

from flask import current_app, render_template
from flask_mail import Mail, Message

mail = Mail()


def init_mail(app):
    mail.init_app(app)


def _send(subject, recipients, html_body):
    if not recipients:
        return

    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        print("=" * 60)
        print(f"[DEV EMAIL - not actually sent] To: {recipients}")
        print(f"Subject: {subject}")
        print("-" * 60)
        print(html_body)
        print("=" * 60)
        return

    try:
        msg = Message(subject=subject, recipients=recipients, html=html_body)
        mail.send(msg)
    except Exception as exc:  # noqa: BLE001 - never let a mail failure break checkout/register
        print(f"[mailer] Failed to send '{subject}' to {recipients}: {exc}")


def send_otp_email(to_email, fullname, otp_code, minutes_valid=10):
    subject = "Your Loop & Love verification code"
    html = render_template(
        "emails/otp.html",
        fullname=fullname,
        otp_code=otp_code,
        minutes_valid=minutes_valid
    )
    _send(subject, [to_email], html)


def send_password_reset_email(to_email, fullname, reset_url, minutes_valid=30):
    subject = "Reset your Loop & Love password"
    html = render_template(
        "emails/password_reset.html",
        fullname=fullname,
        reset_url=reset_url,
        minutes_valid=minutes_valid
    )
    _send(subject, [to_email], html)


def send_order_confirmation_email(order):
    subject = f"Order {order.order_number} confirmed — Loop & Love"
    html = render_template("emails/order_confirmation.html", order=order)
    _send(subject, [order.user.email], html)


def send_admin_new_order_email(order):
    admin_email = current_app.config.get("ADMIN_NOTIFY_EMAIL")
    subject = f"New order {order.order_number} — ₹{order.total:.0f}"
    html = render_template("emails/admin_new_order.html", order=order)
    _send(subject, [admin_email], html)
