from flask import Blueprint, render_template

from database.models import Product


# ==========================================
# PRODUCTS BLUEPRINT
# ==========================================

products = Blueprint("products", __name__)


# ==========================================
# SHOP PAGE
# ==========================================

@products.route("/shop")
def shop():

    all_products = Product.query.filter_by(is_active=True).all()

    return render_template(
        "shop.html",
        products=all_products
    )


# ==========================================
# SINGLE PRODUCT PAGE
# ==========================================

@products.route("/product/<int:product_id>")
def product_details(product_id):

    product = Product.query.get_or_404(product_id)

    related_products = (
        Product.query.filter(
            Product.category == product.category,
            Product.id != product.id,
            Product.is_active == True
        )
        .limit(3)
        .all()
    )

    return render_template(
        "product.html",
        product=product,
        related_products=related_products
    )


# ==========================================
# CATEGORY PAGE
# ==========================================

@products.route("/category/<string:category>")
def category(category):

    products_list = Product.query.filter_by(
        category=category,
        is_active=True
    ).all()

    return render_template(
        "shop.html",
        products=products_list
    )


# ==========================================
# FEATURED PRODUCTS
# ==========================================

@products.route("/featured")
def featured_products():

    featured = Product.query.filter_by(
        featured=True,
        is_active=True
    ).all()

    return render_template(
        "shop.html",
        products=featured
    )