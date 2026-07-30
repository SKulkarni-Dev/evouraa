"""
One-off migration for the existing instance/crochet.db so it picks up
the new columns/tables added for payments, shipping addresses, OTP
verification, and admin order management -- without losing the
products/users/orders that are already in there.

Run once, from the vyshweb/ project folder:

    python scripts/migrate_db.py

Safe to run more than once -- it skips anything already present.
"""

import os
import sqlite3

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "instance", "crochet.db")


def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def table_exists(cur, table):
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


def add_column(cur, table, column, ddl_type, default_sql=None):
    if column_exists(cur, table, column):
        print(f"  - {table}.{column} already exists, skipping")
        return

    sql = f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"
    if default_sql is not None:
        sql += f" DEFAULT {default_sql}"

    cur.execute(sql)
    print(f"  + added {table}.{column}")


def main():
    if not os.path.exists(DB_PATH):
        print("No existing database found -- nothing to migrate. "
              "Flask will create a fresh one (with the new schema) on next run.")
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    print("Migrating users table...")
    add_column(cur, "users", "is_verified", "BOOLEAN", "0")
    # Anyone already in the table pre-dates OTP verification -- treat
    # them as already verified so existing accounts can still log in.
    cur.execute("UPDATE users SET is_verified = 1 WHERE is_verified IS NULL OR is_verified = 0")

    print("Migrating orders table...")
    add_column(cur, "orders", "order_number", "VARCHAR(40)")
    add_column(cur, "orders", "payment_method", "VARCHAR(30)", "'Razorpay'")
    add_column(cur, "orders", "razorpay_order_id", "VARCHAR(64)")
    add_column(cur, "orders", "razorpay_payment_id", "VARCHAR(64)")
    add_column(cur, "orders", "razorpay_signature", "VARCHAR(128)")
    add_column(cur, "orders", "shipping_name", "VARCHAR(100)")
    add_column(cur, "orders", "shipping_phone", "VARCHAR(15)")
    add_column(cur, "orders", "shipping_line1", "VARCHAR(200)")
    add_column(cur, "orders", "shipping_line2", "VARCHAR(200)")
    add_column(cur, "orders", "shipping_city", "VARCHAR(80)")
    add_column(cur, "orders", "shipping_state", "VARCHAR(80)")
    add_column(cur, "orders", "shipping_pincode", "VARCHAR(10)")
    add_column(cur, "orders", "shipping_country", "VARCHAR(56)", "'India'")
    add_column(cur, "orders", "cancelled_at", "DATETIME")

    # Backfill order numbers for any pre-existing orders so the
    # unique index doesn't collide on a bunch of NULLs.
    cur.execute("SELECT id, created_at FROM orders WHERE order_number IS NULL ORDER BY id")
    rows = cur.fetchall()
    for order_id, created_at in rows:
        date_part = (created_at or "19700101")[:10].replace("-", "") or "19700101"
        order_number = f"VYSH-{date_part}-{order_id:04d}"
        cur.execute("UPDATE orders SET order_number = ? WHERE id = ?", (order_number, order_id))
        print(f"  + backfilled order {order_id} -> {order_number}")

    print("Recreating otp table with new columns...")
    # The OTP table's shape changed (phone -> identifier/purpose/attempts).
    # It only ever holds short-lived codes, so it's safe to drop and
    # recreate rather than migrate column-by-column.
    if table_exists(cur, "otp"):
        cur.execute("DROP TABLE otp")
    cur.execute("""
        CREATE TABLE otp (
            id INTEGER PRIMARY KEY,
            identifier VARCHAR(120) NOT NULL,
            purpose VARCHAR(30) NOT NULL DEFAULT 'register',
            otp VARCHAR(6) NOT NULL,
            attempts INTEGER DEFAULT 0,
            is_used BOOLEAN DEFAULT 0,
            created_at DATETIME,
            expires_at DATETIME
        )
    """)

    print("Creating password_reset_tokens table if missing...")
    if not table_exists(cur, "password_reset_tokens"):
        cur.execute("""
            CREATE TABLE password_reset_tokens (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                token VARCHAR(64) NOT NULL UNIQUE,
                is_used BOOLEAN DEFAULT 0,
                created_at DATETIME,
                expires_at DATETIME NOT NULL
            )
        """)

    con.commit()

    print("Adding unique index on orders.order_number (if missing)...")
    try:
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_order_number ON orders(order_number)")
        con.commit()
    except sqlite3.Error as exc:
        print(f"  ! could not create unique index yet: {exc}")

    con.close()
    print("Migration complete.")


if __name__ == "__main__":
    main()
