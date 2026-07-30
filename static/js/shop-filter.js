/*=========================================
LOOP & LOVE - SHOP-FILTER.JS
Client-side search, category filter and sort
for the shop grid. Works on the product-card
data attributes rendered by shop.html.
=========================================*/

document.addEventListener("DOMContentLoaded", () => {

    const grid = document.getElementById("shop-grid");
    if (!grid) return;

    const cards = Array.from(grid.querySelectorAll(".product-card"));
    const searchInput = document.getElementById("shop-search");
    const categorySelect = document.getElementById("shop-category");
    const sortSelect = document.getElementById("shop-sort");
    const noResults = document.getElementById("shop-no-results");

    function applyFilters() {

        const query = (searchInput?.value || "").trim().toLowerCase();
        const category = categorySelect?.value || "";
        let visibleCount = 0;

        cards.forEach(card => {
            const matchesQuery = !query || card.dataset.name.includes(query);
            const matchesCategory = !category || card.dataset.category === category;
            const visible = matchesQuery && matchesCategory;

            card.style.display = visible ? "" : "none";
            if (visible) visibleCount++;
        });

        if (noResults) {
            noResults.style.display = visibleCount === 0 ? "block" : "none";
        }
    }

    function applySort() {

        const sortBy = sortSelect?.value || "";
        if (!sortBy) return;

        const sorted = [...cards].sort((a, b) => {
            if (sortBy === "price-asc") return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
            if (sortBy === "price-desc") return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
            if (sortBy === "rating-desc") return parseFloat(b.dataset.rating) - parseFloat(a.dataset.rating);
            return 0;
        });

        sorted.forEach(card => grid.appendChild(card));
    }

    searchInput?.addEventListener("input", applyFilters);
    categorySelect?.addEventListener("change", applyFilters);
    sortSelect?.addEventListener("change", applySort);
});
