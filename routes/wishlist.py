from flask import Blueprint, jsonify, session

from database.database import db
from database.models import Wishlist, Product
from routes.auth_guard import api_login_required

wishlist_bp = Blueprint("wishlist_bp", __name__)


@wishlist_bp.route("/wishlist/toggle/<int:product_id>", methods=["POST"])
@api_login_required
def toggle_wishlist(product_id):

    product = Product.query.get(product_id)

    if not product:
        return jsonify(success=False, message="Product not found."), 404

    existing = Wishlist.query.filter_by(
        user_id=session["user_id"],
        product_id=product_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify(success=True, added=False)

    db.session.add(Wishlist(user_id=session["user_id"], product_id=product_id))
    db.session.commit()

    return jsonify(success=True, added=True)
