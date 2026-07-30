from datetime import datetime, time

from flask import current_app

from database.models import Order


def next_order_number():
    """Builds e.g. 'VYSH-20260730-0001' -- sequential per calendar day.

    Must be called BEFORE the new Order is added to the session,
    so it counts only orders that already exist. Two checkouts
    landing in the same instant could in theory collide on the
    unique order_number column -- the caller should catch that
    IntegrityError and retry once.
    """

    prefix = current_app.config.get("ORDER_PREFIX", "VYSH")
    today = datetime.utcnow().date()
    day_start = datetime.combine(today, time.min)
    day_end = datetime.combine(today, time.max)

    count_today = Order.query.filter(
        Order.created_at >= day_start,
        Order.created_at <= day_end
    ).count()

    sequence = count_today + 1
    date_part = today.strftime("%Y%m%d")

    return f"{prefix}-{date_part}-{sequence:04d}"
