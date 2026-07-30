# Loop & Love — Setup Notes (New Features)

This build adds payments, order/shipping tracking, email OTP + password
reset, and an admin panel on top of the original store. Nothing here
breaks if you don't configure it yet — see "Works out of the box" below.

## 1. Install dependencies

```
pip install -r requirements.txt
```

(New: `python-dotenv`, `razorpay`, `Flask-Mail`.)

## 2. Set up your .env file

```
cp .env.example .env
```

Then fill in what you have. Everything is optional at first:

- **RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET** — from your Razorpay
  dashboard (Settings → API Keys). Until these are filled in,
  checkout will show a friendly "payments not configured" message
  instead of creating an order.
- **MAIL_ENABLED / MAIL_USERNAME / MAIL_PASSWORD** — SMTP creds for
  sending real emails. Until `MAIL_ENABLED=true` and these are set,
  every email (OTP, password reset, order confirmation, new-order
  alert) is printed to your terminal instead of sent — so you can
  still test the full flow locally by copying the OTP/link out of
  the console.
- **ADMIN_USERNAME / ADMIN_PASSWORD** — login for `/admin/login`.
  Defaults to `admin` / `change-me-now` — **change this** before
  deploying anywhere public.

## 3. Migrate your existing database

Your `instance/crochet.db` already has products/users/orders in it, so
run the one-off migration instead of deleting it:

```
python scripts/migrate_db.py
```

This adds the new columns (order numbers, shipping address, Razorpay
fields, etc.) without touching your existing data. Safe to re-run.

If you'd rather start fresh, just delete `instance/crochet.db` — Flask
will recreate it with the new schema on next run.

## 4. Run it

```
python app.py
```

## What's new

- **Payments (Razorpay)** — checkout now creates a Razorpay order and
  opens the Razorpay Checkout overlay. The payment is only marked
  "Paid" after the server independently verifies the payment
  signature (`utils/razorpay_client.py`) — nothing from the browser
  is trusted directly.
- **Order confirmation email** — sent to the customer once payment
  is verified.
- **New order email** — sent to `ADMIN_NOTIFY_EMAIL` at the same time.
- **Shipping address** — captured on the checkout page and saved with
  every order (`Order.shipping_*` columns).
- **Order numbers** — human-friendly `VYSH-YYYYMMDD-0001` format,
  sequential per day.
- **Payment verified before success** — `/order/success/<id>` redirects
  back to the payment page if `payment_status != "Paid"`, so a shopper
  can't reach the success page by guessing a URL.
- **Forgot password** — `/forgot-password` emails a reset link, valid
  30 minutes, single-use.
- **Email OTP on registration** — new accounts start unverified, get a
  6-digit code emailed to them, and can't log in until they verify at
  `/verify-otp`. Unverified logins get a fresh code and are redirected
  there too.
- **Admin panel** (`/admin/login`) — separate hardcoded credentials
  (not your shopper accounts). Lets staff view all orders, filter by
  status, and update order status (Processing → Packed → Shipped →
  Delivered → Cancelled) and payment status (Pending/Paid/Failed/
  Refunded).
- **Cancel order** — customers can cancel their own order from
  `/profile` as long as it hasn't shipped yet; admins can cancel from
  the admin panel too. Cancelling restores stock automatically.

## Known limitations / things to revisit later

- Stock is decremented as soon as an order is placed (before payment
  is confirmed), matching the original app's behavior. If a shopper
  abandons the Razorpay popup, that stock stays reserved until they
  either complete payment or cancel the order themselves. For a small
  catalog this is usually fine; a production store would want a
  background job to auto-cancel unpaid orders after N minutes.
- Order numbering counts orders created "today" in a simple query —
  fine at this scale, but a dedicated counter table would be safer
  under heavy concurrent traffic.
- The admin panel has no CSRF protection or rate limiting on the
  login form (Flask-WTF is already a dependency if you want to add
  CSRF tokens to these forms).
