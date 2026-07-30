(function () {
    const payBtn = document.getElementById("payNowBtn");

    if (!payBtn) return;

    function openRazorpay() {
        if (!RAZORPAY_KEY_ID) {
            alert("Payments aren't configured on this store yet. Please contact the site owner.");
            return;
        }

        const options = {
            key: RAZORPAY_KEY_ID,
            amount: AMOUNT_PAISE,
            currency: "INR",
            name: "Loop & Love",
            description: "Order payment",
            order_id: RAZORPAY_ORDER_ID,
            prefill: {
                name: CUSTOMER_NAME,
                email: CUSTOMER_EMAIL,
                contact: CUSTOMER_PHONE
            },
            theme: { color: "#7B2D3E" },
            handler: function (response) {
                fetch(VERIFY_URL, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        order_id: ORDER_ID,
                        razorpay_order_id: response.razorpay_order_id,
                        razorpay_payment_id: response.razorpay_payment_id,
                        razorpay_signature: response.razorpay_signature
                    })
                })
                    .then((res) => res.json())
                    .then((data) => {
                        if (data.success) {
                            window.location.href = data.redirect_url;
                        } else {
                            alert(data.message || "Payment verification failed.");
                        }
                    })
                    .catch(() => {
                        alert("Couldn't verify your payment. If money was deducted, it will be refunded automatically.");
                    });
            },
            modal: {
                ondismiss: function () {
                    // User closed the widget without paying -- leave the
                    // order as Pending so they can retry with the same button.
                }
            }
        };

        const rzp = new Razorpay(options);

        rzp.on("payment.failed", function () {
            fetch(FAILED_URL, { method: "POST" }).finally(() => {
                window.location.reload();
            });
        });

        rzp.open();
    }

    payBtn.addEventListener("click", openRazorpay);

    // Open automatically on page load for a smoother flow.
    openRazorpay();
})();
