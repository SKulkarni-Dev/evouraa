from datetime import datetime

from database.database import db


# ==========================================
# USER TABLE
# ==========================================

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    fullname = db.Column(db.String(100), nullable=False)

    phone = db.Column(
        db.String(15),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Set True once the registration OTP has been confirmed.
    is_verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    # Relationships

    wishlist = db.relationship(
        "Wishlist",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    cart = db.relationship(
        "Cart",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    orders = db.relationship(
        "Order",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )


# ==========================================
# OTP TABLE
# Generic one-time-passcode store, reused for both
# registration email verification and (in future) phone OTP.
# `purpose` keeps the same table usable for more than one flow.
# ==========================================

class OTP(db.Model):

    __tablename__ = "otp"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Email (or phone) the OTP was sent to.
    identifier = db.Column(
        db.String(120),
        nullable=False,
        index=True
    )

    purpose = db.Column(
        db.String(30),
        nullable=False,
        default="register"
    )

    otp = db.Column(
        db.String(6),
        nullable=False
    )

    attempts = db.Column(
        db.Integer,
        default=0
    )

    is_used = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    expires_at = db.Column(
        db.DateTime
    )


# ==========================================
# PASSWORD RESET TOKEN TABLE
# ==========================================

class PasswordResetToken(db.Model):

    __tablename__ = "password_reset_tokens"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    token = db.Column(
        db.String(64),
        nullable=False,
        unique=True,
        index=True
    )

    is_used = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    user = db.relationship("User")


# ==========================================
# PRODUCT TABLE
# ==========================================

class Product(db.Model):

    __tablename__ = "products"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    image = db.Column(
        db.String(255)
    )

    stock = db.Column(
        db.Integer,
        default=0
    )

    category = db.Column(
        db.String(100)
    )

    featured = db.Column(
        db.Boolean,
        default=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    rating = db.Column(
        db.Float,
        default=0.0
    )

    reviews = db.Column(
        db.Integer,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ==========================================
# WISHLIST TABLE
# ==========================================

class Wishlist(db.Model):

    __tablename__ = "wishlist"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    product = db.relationship("Product")


# ==========================================
# CART TABLE
# ==========================================

class Cart(db.Model):

    __tablename__ = "cart"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        default=1
    )

    product = db.relationship("Product")


# ==========================================
# ORDER TABLE
# ==========================================

class Order(db.Model):

    __tablename__ = "orders"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Human-facing reference, e.g. "VYSH-20260730-0001".
    # The numeric id above still drives foreign keys internally.
    order_number = db.Column(
        db.String(40),
        unique=True,
        index=True
    )

    total = db.Column(
        db.Float,
        nullable=False
    )

    # Pending / Paid / Failed / Refunded
    payment_status = db.Column(
        db.String(30),
        default="Pending"
    )

    # Processing / Packed / Shipped / Delivered / Cancelled
    order_status = db.Column(
        db.String(30),
        default="Processing"
    )

    payment_method = db.Column(
        db.String(30),
        default="Razorpay"
    )

    # ---- Razorpay tracking ----
    razorpay_order_id = db.Column(db.String(64))
    razorpay_payment_id = db.Column(db.String(64))
    razorpay_signature = db.Column(db.String(128))

    # ---- Shipping address, captured at the time of the order ----
    # (kept on the order itself, not the user, so past orders still
    # show the correct address even if the user's details change later)
    shipping_name = db.Column(db.String(100))
    shipping_phone = db.Column(db.String(15))
    shipping_line1 = db.Column(db.String(200))
    shipping_line2 = db.Column(db.String(200))
    shipping_city = db.Column(db.String(80))
    shipping_state = db.Column(db.String(80))
    shipping_pincode = db.Column(db.String(10))
    shipping_country = db.Column(db.String(56), default="India")

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    cancelled_at = db.Column(db.DateTime)

    items = db.relationship(
        "OrderItem",
        backref="order",
        lazy=True,
        cascade="all, delete-orphan"
    )


# ==========================================
# ORDER ITEMS TABLE
# ==========================================

class OrderItem(db.Model):

    __tablename__ = "order_items"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        default=1
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    product = db.relationship("Product")