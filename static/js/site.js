/* =====================================================================
   LOOP & LOVE — SITE.JS
   Nav behavior, scroll-reveal, toast feedback, and cart/wishlist
   AJAX calls against the real Flask backend.
   ===================================================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* ---------- Sticky nav frosted state ---------- */

    const header = document.querySelector("header");

    if (header) {
        const onScroll = () => header.classList.toggle("scrolled", window.scrollY > 12);
        onScroll();
        window.addEventListener("scroll", onScroll, { passive: true });
    }

    /* ---------- Mobile nav toggle ---------- */

    const toggle = document.querySelector(".nav-toggle");
    const menu = document.querySelector("header nav > ul");

    if (toggle && menu) {
        toggle.addEventListener("click", () => {
            const isOpen = menu.classList.toggle("open");
            toggle.classList.toggle("open", isOpen);
            toggle.setAttribute("aria-expanded", isOpen);
        });

        menu.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                menu.classList.remove("open");
                toggle.classList.remove("open");
            });
        });
    }

    /* ---------- Scroll reveal ---------- */

    const revealEls = document.querySelectorAll(".reveal");

    if (revealEls.length) {
        const io = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("in");
                    io.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15 });

        revealEls.forEach(el => io.observe(el));
    }

    /* ---------- Toast ---------- */

    let toastEl = document.querySelector(".toast");
    if (!toastEl) {
        toastEl = document.createElement("div");
        toastEl.className = "toast";
        document.body.appendChild(toastEl);
    }

    let toastTimer = null;

    window.showToast = function (message, icon = "fa-circle-check") {
        toastEl.innerHTML = `<i class="fa-solid ${icon}"></i> ${message}`;
        toastEl.classList.add("show");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => toastEl.classList.remove("show"), 2600);
    };

    /* ---------- Nav cart badge ---------- */

    function setCartBadge(count) {
        const badge = document.querySelector(".nav-cart-badge");
        if (!badge) return;
        badge.textContent = count;
        badge.style.display = count > 0 ? "flex" : "none";
    }

    /* ---------- Add to cart ---------- */

    document.querySelectorAll(".add-to-cart-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (btn.disabled) return;

            const productId = btn.dataset.productId;
            const productName = btn.dataset.productName || "Item";
            const qtyEl = document.querySelector(".qty-value");
            const quantity = qtyEl ? parseInt(qtyEl.textContent, 10) || 1 : 1;

            try {
                const res = await fetch(`/cart/add/${productId}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ quantity })
                });

                if (res.status === 401) {
                    window.showToast("Please log in to add items to your cart", "fa-lock");
                    setTimeout(() => window.location.href = "/login", 900);
                    return;
                }

                const data = await res.json();

                if (data.success) {
                    window.showToast(`${productName} added to cart`);
                    setCartBadge(data.cart_count);
                } else {
                    window.showToast(data.message || "Could not add to cart", "fa-circle-exclamation");
                }
            } catch (err) {
                window.showToast("Something went wrong. Try again.", "fa-circle-exclamation");
            }
        });
    });

    /* ---------- Wishlist toggle ---------- */

    document.querySelectorAll(".wish-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.preventDefault();
            e.stopPropagation();

            const productId = btn.dataset.productId;

            try {
                const res = await fetch(`/wishlist/toggle/${productId}`, { method: "POST" });

                if (res.status === 401) {
                    window.showToast("Please log in to save favorites", "fa-lock");
                    setTimeout(() => window.location.href = "/login", 900);
                    return;
                }

                const data = await res.json();
                const icon = btn.querySelector("i");

                if (data.added) {
                    btn.classList.add("active");
                    if (icon) { icon.classList.remove("fa-regular"); icon.classList.add("fa-solid"); }
                    window.showToast("Added to wishlist");
                } else {
                    btn.classList.remove("active");
                    if (icon) { icon.classList.remove("fa-solid"); icon.classList.add("fa-regular"); }
                    window.showToast("Removed from wishlist");
                    if (btn.closest("[data-wishlist-row]")) {
                        btn.closest("[data-wishlist-row]").remove();
                    }
                }
            } catch (err) {
                window.showToast("Something went wrong. Try again.", "fa-circle-exclamation");
            }
        });
    });

    /* ---------- Cart page: quantity + remove ---------- */

    document.querySelectorAll("[data-cart-row]").forEach(row => {
        const productId = row.dataset.productId;
        const minus = row.querySelector(".qty-minus");
        const plus = row.querySelector(".qty-plus");
        const valueEl = row.querySelector(".qty-value");
        const removeBtn = row.querySelector(".remove-btn");
        const lineTotalEl = row.querySelector(".line-total");
        const unitPrice = parseFloat(row.dataset.price || "0");

        async function updateQty(newQty) {
            if (newQty < 1) return;
            const res = await fetch(`/cart/update/${productId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ quantity: newQty })
            });
            const data = await res.json();
            if (data.success) {
                valueEl.textContent = newQty;
                if (lineTotalEl) lineTotalEl.textContent = "₹" + (unitPrice * newQty).toFixed(0);
                updateCartSummary(data);
            }
        }

        minus?.addEventListener("click", () => {
            const current = parseInt(valueEl.textContent, 10) || 1;
            if (current > 1) updateQty(current - 1);
        });

        plus?.addEventListener("click", () => {
            const current = parseInt(valueEl.textContent, 10) || 1;
            updateQty(current + 1);
        });

        removeBtn?.addEventListener("click", async () => {
            const res = await fetch(`/cart/remove/${productId}`, { method: "POST" });
            const data = await res.json();
            if (data.success) {
                row.style.opacity = "0";
                row.style.transform = "translateX(20px)";
                setTimeout(() => {
                    row.remove();
                    updateCartSummary(data);
                    if (data.cart_count === 0) window.location.reload();
                }, 250);
            }
        });
    });

    function updateCartSummary(data) {
        const subtotalEl = document.querySelector(".cart-subtotal");
        const totalEl = document.querySelector(".cart-total");
        const badge = document.querySelector(".nav-cart-badge");
        if (subtotalEl && data.subtotal !== undefined) subtotalEl.textContent = "₹" + data.subtotal.toFixed(0);
        if (totalEl && data.total !== undefined) totalEl.textContent = "₹" + data.total.toFixed(0);
        if (badge) {
            badge.textContent = data.cart_count;
            badge.style.display = data.cart_count > 0 ? "flex" : "none";
        }
    }

    /* ---------- Product page quantity stepper ---------- */

    const qtyMinus = document.querySelector(".product-page .qty-minus");
    const qtyPlus = document.querySelector(".product-page .qty-plus");
    const qtyValue = document.querySelector(".product-page .qty-value");

    if (qtyMinus && qtyPlus && qtyValue) {
        qtyMinus.addEventListener("click", () => {
            let qty = parseInt(qtyValue.textContent, 10) || 1;
            if (qty > 1) qtyValue.textContent = --qty;
        });
        qtyPlus.addEventListener("click", () => {
            let qty = parseInt(qtyValue.textContent, 10) || 1;
            qtyValue.textContent = ++qty;
        });
    }

});
