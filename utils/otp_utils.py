import random
import secrets
from datetime import datetime, timedelta

from database.database import db
from database.models import OTP, PasswordResetToken

OTP_VALID_MINUTES = 10
RESET_TOKEN_VALID_MINUTES = 30
MAX_OTP_ATTEMPTS = 5


def generate_otp(identifier, purpose="register"):
    """Create a fresh 6-digit OTP, invalidating any earlier unused one
    for the same identifier/purpose so only the latest code works."""

    OTP.query.filter_by(identifier=identifier, purpose=purpose, is_used=False).update(
        {"is_used": True}
    )

    code = f"{random.randint(0, 999999):06d}"

    otp = OTP(
        identifier=identifier,
        purpose=purpose,
        otp=code,
        expires_at=datetime.utcnow() + timedelta(minutes=OTP_VALID_MINUTES)
    )
    db.session.add(otp)
    db.session.commit()

    return code


def verify_otp(identifier, purpose, code):
    """Returns (ok: bool, message: str)."""

    otp = (
        OTP.query.filter_by(identifier=identifier, purpose=purpose, is_used=False)
        .order_by(OTP.created_at.desc())
        .first()
    )

    if not otp:
        return False, "No active code found. Please request a new one."

    if otp.expires_at and otp.expires_at < datetime.utcnow():
        return False, "This code has expired. Please request a new one."

    if otp.attempts >= MAX_OTP_ATTEMPTS:
        return False, "Too many incorrect attempts. Please request a new code."

    if otp.otp != code:
        otp.attempts += 1
        db.session.commit()
        return False, "Incorrect code. Please try again."

    otp.is_used = True
    db.session.commit()

    return True, "Verified."


def generate_reset_token(user_id):
    token = secrets.token_urlsafe(32)

    reset = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(minutes=RESET_TOKEN_VALID_MINUTES)
    )
    db.session.add(reset)
    db.session.commit()

    return token


def consume_reset_token(token):
    """Returns the PasswordResetToken if valid+unused+unexpired, else None."""

    reset = PasswordResetToken.query.filter_by(token=token, is_used=False).first()

    if not reset:
        return None

    if reset.expires_at < datetime.utcnow():
        return None

    return reset
