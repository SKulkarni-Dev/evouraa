from flask import Blueprint, jsonify, session, request

from database.database import db
from database.models import Cart, Product
from routes.auth_guard import api_login_required

cart_bp = Blueprint("cart_bp", __name__)


def _cart_summary(user_id):
    """Return (cart_count, subtotal, total) for the current user's cart."""

    items = Cart.query.filter_by(user_id=user_id).all()

    cart_count = sum(item.quantity for item in items)
    subtotal = sum(item.product.price * item.quantity for item in items)

    shipping = 0 if subtotal >= 999 or subtotal == 0 else 79
    total = subtotal + shipping

    return cart_count, subtotal, total


@cart_bp.route("/cart/add/<int:product_id>", methods=["POST"])
@api_login_required
def add_to_cart(product_id):

    product = Product.query.get(product_id)

    if not product or not product.is_active:
        return jsonify(success=False, message="Product not found."), 404

    if product.stock <= 0:
        return jsonify(success=False, message="This item is currently sold out."), 400

    data = request.get_json(silent=True) or {}
    requested_qty = int(data.get("quantity", 1))

    existing = Cart.query.filter_by(user_id=session["user_id"], product_id=product_id).first()

    if existing:
        existing.quantity = min(existing.quantity + requested_qty, product.stock)
    else:
        db.session.add(Cart(
            user_id=session["user_id"],
            product_id=product_id,
            quantity=min(requested_qty, product.stock)
        ))

    db.session.commit()

    cart_count, subtotal, total = _cart_summary(session["user_id"])

    return jsonify(success=True, cart_count=cart_count, subtotal=subtotal, total=total)


@cart_bp.route("/cart/update/<int:product_id>", methods=["POST"])
@api_login_required
def update_cart_item(product_id):

    data = request.get_json(silent=True) or {}
    quantity = int(data.get("quantity", 1))

    item = Cart.query.filter_by(user_id=session["user_id"], product_id=product_id).first()

    if not item:
        return jsonify(success=False, message="Item not in cart."), 404

    if quantity < 1:
        db.session.delete(item)
    else:
        item.quantity = min(quantity, item.product.stock or quantity)

    db.session.commit()

    cart_count, subtotal, total = _cart_summary(session["user_id"])

    return jsonify(success=True, cart_count=cart_count, subtotal=subtotal, total=total)


@cart_bp.route("/cart/remove/<int:product_id>", methods=["POST"])
@api_login_required
def remove_cart_item(product_id):

    item = Cart.query.filter_by(user_id=session["user_id"], product_id=product_id).first()

    if item:
        db.session.delete(item)
        db.session.commit()

    cart_count, subtotal, total = _cart_summary(session["user_id"])

    return jsonify(success=True, cart_count=cart_count, subtotal=subtotal, total=total)
