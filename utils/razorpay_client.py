import razorpay
from flask import current_app


def get_client():
    key_id = current_app.config.get("RAZORPAY_KEY_ID")
    key_secret = current_app.config.get("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        return None

    return razorpay.Client(auth=(key_id, key_secret))


def create_razorpay_order(amount_rupees, receipt):
    """Creates a Razorpay order for the given rupee amount.
    Returns the Razorpay order dict, or None if keys aren't configured."""

    client = get_client()

    if client is None:
        return None

    return client.order.create({
        "amount": int(round(amount_rupees * 100)),  # paise
        "currency": "INR",
        "receipt": receipt,
        "payment_capture": 1
    })


def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    client = get_client()

    if client is None:
        return False

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
