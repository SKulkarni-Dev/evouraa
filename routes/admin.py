from datetime import datetime
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, current_app
)

from database.database import db
from database.models import Order

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")

ORDER_STATUS_FLOW = ["Processing", "Packed", "Shipped", "Delivered"]
PAYMENT_STATUSES = ["Pending", "Paid", "Failed", "Refunded"]


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_bp.admin_login"))
        return view(*args, **kwargs)
    return wrapped


# ==========================================
# ADMIN LOGIN
# Separate, hardcoded credentials (ADMIN_USERNAME / ADMIN_PASSWORD
# in .env) -- intentionally not tied to the shopper "users" table.
# ==========================================

@admin_bp.route("/login", methods=["GET"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("admin_bp.orders"))
    return render_template("admin/login.html")


@admin_bp.route("/login", methods=["POST"])
def admin_login_submit():

    username = request.form.get("username")
    password = request.form.get("password")

    valid = (
        username == current_app.config.get("ADMIN_USERNAME")
        and password == current_app.config.get("ADMIN_PASSWORD")
    )

    if not valid:
        flash("Invalid admin credentials.", "danger")
        return redirect(url_for("admin_bp.admin_login"))

    session["is_admin"] = True
    flash("Welcome back.", "success")
    return redirect(url_for("admin_bp.orders"))


@admin_bp.route("/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out of admin.", "success")
    return redirect(url_for("admin_bp.admin_login"))


# ==========================================
# ORDER MANAGEMENT
# ==========================================

@admin_bp.route("/orders")
@admin_required
def orders():

    status_filter = request.args.get("status", "")

    query = Order.query.order_by(Order.created_at.desc())

    if status_filter:
        query = query.filter_by(order_status=status_filter)

    all_orders = query.all()

    return render_template(
        "admin/orders.html",
        orders=all_orders,
        status_filter=status_filter,
        statuses=ORDER_STATUS_FLOW + ["Cancelled"]
    )


@admin_bp.route("/orders/<int:order_id>")
@admin_required
def order_detail(order_id):

    order = Order.query.get_or_404(order_id)

    return render_template(
        "admin/order_detail.html",
        order=order,
        order_statuses=ORDER_STATUS_FLOW + ["Cancelled"],
        payment_statuses=PAYMENT_STATUSES
    )


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("order_status")

    if new_status not in ORDER_STATUS_FLOW + ["Cancelled"]:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin_bp.order_detail", order_id=order_id))

    if new_status == "Cancelled" and order.order_status != "Cancelled":
        for item in order.items:
            if item.product and item.product.stock is not None:
                item.product.stock += item.quantity
        order.cancelled_at = datetime.utcnow()
        if order.payment_status == "Paid":
            order.payment_status = "Refunded"

    order.order_status = new_status
    db.session.commit()

    flash(f"Order {order.order_number} marked as {new_status}.", "success")
    return redirect(url_for("admin_bp.order_detail", order_id=order_id))


@admin_bp.route("/orders/<int:order_id>/payment-status", methods=["POST"])
@admin_required
def update_payment_status(order_id):

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("payment_status")

    if new_status not in PAYMENT_STATUSES:
        flash("Invalid payment status.", "danger")
        return redirect(url_for("admin_bp.order_detail", order_id=order_id))

    order.payment_status = new_status
    db.session.commit()

    flash(f"Payment status for {order.order_number} set to {new_status}.", "success")
    return redirect(url_for("admin_bp.order_detail", order_id=order_id))
