from datetime import datetime

from flask import (
    Blueprint, render_template, session, redirect,
    url_for, flash, request, current_app, jsonify
)
from sqlalchemy.exc import IntegrityError

from database.database import db
from database.models import Cart, Order, OrderItem, User
from routes.auth_guard import login_required
from utils.order_utils import next_order_number
from utils.razorpay_client import create_razorpay_order, verify_payment_signature
from utils.mailer import send_order_confirmation_email, send_admin_new_order_email

checkout_bp = Blueprint("checkout_bp", __name__)

REQUIRED_ADDRESS_FIELDS = [
    "shipping_name", "shipping_phone", "shipping_line1",
    "shipping_city", "shipping_state", "shipping_pincode"
]


def _cart_totals(items):
    subtotal = sum(item.product.price * item.quantity for item in items)
    shipping = 0 if subtotal >= 999 or subtotal == 0 else 79
    return subtotal, shipping, subtotal + shipping


@checkout_bp.route("/checkout")
@login_required
def checkout():

    items = Cart.query.filter_by(user_id=session["user_id"]).all()

    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart"))

    subtotal, shipping, total = _cart_totals(items)
    user = User.query.get(session["user_id"])

    return render_template(
        "checkout.html",
        items=items,
        subtotal=subtotal,
        shipping=shipping,
        total=total,
        user=user
    )


@checkout_bp.route("/checkout/place", methods=["POST"])
@login_required
def place_order():

    items = Cart.query.filter_by(user_id=session["user_id"]).all()

    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart"))

    address = {field: (request.form.get(field) or "").strip() for field in REQUIRED_ADDRESS_FIELDS}
    address["shipping_line2"] = (request.form.get("shipping_line2") or "").strip()
    address["shipping_country"] = (request.form.get("shipping_country") or "India").strip()

    missing = [f for f in REQUIRED_ADDRESS_FIELDS if not address[f]]
    if missing:
        flash("Please fill in your complete shipping address.", "danger")
        return redirect(url_for("checkout_bp.checkout"))

    # Re-check stock at the moment of ordering, not just at add-to-cart time.
    for item in items:
        if item.product.stock is not None and item.quantity > item.product.stock:
            flash(f"Only {item.product.stock} left of {item.product.name} -- please update your cart.", "warning")
            return redirect(url_for("cart"))

    subtotal, shipping, total = _cart_totals(items)

    order_number = next_order_number()

    razorpay_order = create_razorpay_order(total, receipt=order_number)

    if razorpay_order is None:
        flash(
            "Online payment isn't configured yet on this store "
            "(missing Razorpay keys). Please contact the site owner.",
            "danger"
        )
        return redirect(url_for("checkout_bp.checkout"))

    order = Order(
        user_id=session["user_id"],
        order_number=order_number,
        total=total,
        payment_status="Pending",
        order_status="Processing",
        payment_method="Razorpay",
        razorpay_order_id=razorpay_order["id"],
        shipping_name=address["shipping_name"],
        shipping_phone=address["shipping_phone"],
        shipping_line1=address["shipping_line1"],
        shipping_line2=address["shipping_line2"],
        shipping_city=address["shipping_city"],
        shipping_state=address["shipping_state"],
        shipping_pincode=address["shipping_pincode"],
        shipping_country=address["shipping_country"]
    )

    try:
        db.session.add(order)
        db.session.flush()

        for item in items:
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            ))

            if item.product.stock is not None:
                item.product.stock = max(item.product.stock - item.quantity, 0)

            db.session.delete(item)

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Something went wrong placing your order. Please try again.", "danger")
        return redirect(url_for("checkout_bp.checkout"))

    return redirect(url_for("checkout_bp.pay", order_id=order.id))


@checkout_bp.route("/checkout/pay/<int:order_id>")
@login_required
def pay(order_id):
    """Shows the Razorpay Checkout overlay for an order awaiting payment."""

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first_or_404()

    if order.payment_status == "Paid":
        return redirect(url_for("checkout_bp.order_success", order_id=order.id))

    if order.order_status == "Cancelled":
        flash("This order has been cancelled.", "warning")
        return redirect(url_for("profile"))

    user = User.query.get(session["user_id"])

    return render_template(
        "checkout_pay.html",
        order=order,
        user=user,
        razorpay_key_id=current_app.config.get("RAZORPAY_KEY_ID")
    )


@checkout_bp.route("/checkout/verify", methods=["POST"])
@login_required
def verify_payment():
    """Called via fetch() by the Razorpay Checkout success handler.
    Nothing is marked as paid until the signature checks out server-side."""

    data = request.get_json(silent=True) or {}

    order_id = data.get("order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_signature = data.get("razorpay_signature")

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first()

    if not order:
        return jsonify(success=False, message="Order not found."), 404

    if order.razorpay_order_id != razorpay_order_id:
        return jsonify(success=False, message="Order mismatch."), 400

    valid = verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

    if not valid:
        order.payment_status = "Failed"
        db.session.commit()
        return jsonify(success=False, message="Payment verification failed."), 400

    order.payment_status = "Paid"
    order.razorpay_payment_id = razorpay_payment_id
    order.razorpay_signature = razorpay_signature
    db.session.commit()

    send_order_confirmation_email(order)
    send_admin_new_order_email(order)

    return jsonify(success=True, redirect_url=url_for("checkout_bp.order_success", order_id=order.id))


@checkout_bp.route("/checkout/failed/<int:order_id>", methods=["POST"])
@login_required
def payment_failed(order_id):
    """Called when the Razorpay modal reports a failed payment (not just
    dismissed) so the order doesn't sit as an ambiguous 'Pending' forever."""

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first_or_404()

    if order.payment_status != "Paid":
        order.payment_status = "Failed"
        db.session.commit()

    flash("Payment failed. You can try again below.", "danger")
    return redirect(url_for("checkout_bp.pay", order_id=order.id))


@checkout_bp.route("/order/success/<int:order_id>")
@login_required
def order_success(order_id):

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first_or_404()

    if order.payment_status != "Paid":
        return redirect(url_for("checkout_bp.pay", order_id=order.id))

    return render_template("order_success.html", order=order)


@checkout_bp.route("/order/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):

    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first_or_404()

    if order.order_status in ("Shipped", "Delivered", "Cancelled"):
        flash("This order can no longer be cancelled.", "warning")
        return redirect(url_for("profile"))

    for item in order.items:
        if item.product and item.product.stock is not None:
            item.product.stock += item.quantity

    order.order_status = "Cancelled"
    order.cancelled_at = datetime.utcnow()

    if order.payment_status == "Paid":
        order.payment_status = "Refunded"

    db.session.commit()

    flash(f"Order {order.order_number} has been cancelled.", "success")
    return redirect(url_for("profile"))
