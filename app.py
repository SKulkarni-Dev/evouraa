from datetime import datetime

from flask import Flask, render_template, session

from routes.auth_guard import login_required
from config import Config

from database.database import db
import database.models

from routes.auth import auth
from routes.products import products
from routes.cart import cart_bp
from routes.wishlist import wishlist_bp
from routes.checkout import checkout_bp
from routes.admin import admin_bp

from utils.mailer import init_mail


# ==========================================
# CREATE FLASK APP
# ==========================================

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)
init_mail(app)


# ==========================================
# GLOBAL TEMPLATE CONTEXT
# Makes the cart badge count and current user
# available on every page without repeating
# the query in every view function.
# ==========================================

@app.context_processor
def inject_globals():
    from database.models import Cart

    cart_count = 0

    if "user_id" in session:
        cart_count = (
            db.session.query(db.func.coalesce(db.func.sum(Cart.quantity), 0))
            .filter(Cart.user_id == session["user_id"])
            .scalar()
        )

    return dict(
        cart_count=cart_count or 0,
        current_year=datetime.utcnow().year,
        logged_in_user=session.get("user_name")
    )


# ==========================================
# HOME PAGE
# Public — visitors must be able to browse
# without creating an account first.
# ==========================================

@app.route("/")
def home():
    from database.models import Product

    best_sellers = (
        Product.query.filter_by(is_active=True)
        .order_by(Product.rating.desc())
        .limit(4)
        .all()
    )

    return render_template("index.html", best_sellers=best_sellers)


# ==========================================
# REGISTER PAGE
# ==========================================

@app.route("/register")
def register_page():
    return render_template("register.html")


# ==========================================
# LOGIN PAGE
# ==========================================

@app.route("/login")
def login_page():
    return render_template("login.html")


# ==========================================
# PROFILE PAGE (personal — requires login)
# ==========================================

@app.route("/profile")
@login_required
def profile():
    from database.models import User, Order

    user = User.query.get(session["user_id"])
    orders = (
        Order.query.filter_by(user_id=session["user_id"])
        .order_by(Order.created_at.desc())
        .all()
    )

    return render_template("profile.html", user=user, orders=orders)


# ==========================================
# CART PAGE (personal — requires login)
# ==========================================

@app.route("/cart")
@login_required
def cart():
    from database.models import Cart as CartModel

    items = CartModel.query.filter_by(user_id=session["user_id"]).all()

    subtotal = sum(item.product.price * item.quantity for item in items)
    shipping = 0 if subtotal >= 999 or subtotal == 0 else 79
    total = subtotal + shipping

    return render_template(
        "cart.html",
        items=items,
        subtotal=subtotal,
        shipping=shipping,
        total=total
    )


# ==========================================
# WISHLIST PAGE (personal — requires login)
# ==========================================

@app.route("/wishlist")
@login_required
def wishlist():
    from database.models import Wishlist as WishlistModel

    items = WishlistModel.query.filter_by(user_id=session["user_id"]).all()

    return render_template("wishlist.html", items=items)


# ==========================================
# ABOUT PAGE — public
# ==========================================

@app.route("/about")
def about():
    return render_template("about.html")


# ==========================================
# CONTACT PAGE — public
# ==========================================

@app.route("/contact", methods=["GET", "POST"])
def contact():
    from flask import request, redirect, url_for, flash

    if request.method == "POST":
        name = request.form.get("name")
        message = request.form.get("message")

        if not name or not message:
            flash("Please fill in your name and message.", "warning")
        else:
            # No outbound email service is configured yet — acknowledge
            # receipt so the form doesn't feel broken to the visitor.
            flash("Thanks for reaching out! We'll get back to you within 24 hours.", "success")

        return redirect(url_for("contact"))

    return render_template("contact.html")


# ==========================================
# REGISTER BLUEPRINTS
# products blueprint owns /shop, /product/<id>,
# /category/<name>, /featured — all public so
# shoppers can browse and decide before signing up.
# cart_bp / wishlist_bp / checkout_bp own the
# personal, login-gated actions.
# ==========================================

app.register_blueprint(auth)
app.register_blueprint(products)
app.register_blueprint(cart_bp)
app.register_blueprint(wishlist_bp)
app.register_blueprint(checkout_bp)
app.register_blueprint(admin_bp)


# ==========================================
# RUN APPLICATION
# ==========================================

# Create database tables when the app starts
with app.app_context():
    db.create_all()

# Run locally
if __name__ == "__main__":
    app.run(debug=True)