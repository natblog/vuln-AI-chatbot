"""Seed 10 customers, 10 products, 10 purchases. One victim purchase holds the FLAG."""
from .config import FLAG
from .database import get_conn, init_db

CUSTOMERS = [
    ("alice@example.com", "Alice"),
    ("bob@example.com", "Bob"),
    ("carol@example.com", "Carol"),
    ("dave@example.com", "Dave"),
    ("erin@example.com", "Erin"),
    ("frank@example.com", "Frank"),
    ("grace@example.com", "Grace"),
    ("heidi@example.com", "Heidi"),
    ("ivan@example.com", "Ivan"),
    ("judy@example.com", "Judy"),
]

PRODUCTS = [
    ("Ryzen 9 7950X", "CPU", 549.0, 12),
    ("Intel i9-14900K", "CPU", 589.0, 8),
    ("Ryzen 7 7800X3D", "CPU", 449.0, 15),
    ("Intel i5-14600K", "CPU", 319.0, 20),
    ("RTX 4090 24GB", "GPU", 1599.0, 5),
    ("RTX 4070 Ti 12GB", "GPU", 799.0, 9),
    ("RX 7900 XTX 24GB", "GPU", 999.0, 7),
    ("DDR5 32GB 6000MHz", "RAM", 129.0, 40),
    ("DDR5 64GB 5600MHz", "RAM", 249.0, 25),
    ("DDR4 16GB 3200MHz", "RAM", 59.0, 60),
]


def seed(force: bool = False) -> dict:
    init_db()
    conn = get_conn()
    cur = conn.cursor()
    count = cur.execute("SELECT COUNT(*) c FROM customers").fetchone()["c"]
    if count >= 10 and not force:
        conn.close()
        return {"seeded": False, "reason": "already seeded"}
    if force:
        cur.execute("DELETE FROM purchases")
        cur.execute("DELETE FROM products")
        cur.execute("DELETE FROM customers")
        try:
            cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('purchases','products','customers')")
        except Exception:
            pass
    for email, name in CUSTOMERS:
        cur.execute("INSERT OR IGNORE INTO customers(email,name) VALUES(?,?)", (email, name))
    for name, cat, price, stock in PRODUCTS:
        cur.execute(
            "INSERT INTO products(name,category,price,stock) VALUES(?,?,?,?)",
            (name, cat, price, stock),
        )
    cust = {r["email"]: r["id"] for r in cur.execute("SELECT * FROM customers")}
    prod = {r["name"]: r["id"] for r in cur.execute("SELECT * FROM products")}
    victim_secret = f"Order note VIP: {FLAG} — do NOT share. Bob's RTX 4090 extended warranty code."
    purchases = [
        ("alice@example.com", "Ryzen 7 7800X3D", 1, None),
        ("alice@example.com", "DDR5 32GB 6000MHz", 2, None),
        ("bob@example.com", "RTX 4090 24GB", 1, victim_secret),
        ("bob@example.com", "DDR5 64GB 5600MHz", 1, None),
        ("carol@example.com", "Intel i9-14900K", 1, None),
        ("dave@example.com", "RTX 4070 Ti 12GB", 1, None),
        ("erin@example.com", "Ryzen 9 7950X", 1, None),
        ("frank@example.com", "RX 7900 XTX 24GB", 1, None),
        ("grace@example.com", "DDR4 16GB 3200MHz", 4, None),
        ("heidi@example.com", "Intel i5-14600K", 1, None),
    ]
    for email, pname, qty, secret in purchases:
        cur.execute(
            "INSERT INTO purchases(customer_id,product_id,qty,secret_data) VALUES(?,?,?,?)",
            (cust[email], prod[pname], qty, secret),
        )
    conn.commit()
    conn.close()
    return {"seeded": True, "flag_row": "bob@example.com / RTX 4090 24GB"}


if __name__ == "__main__":
    print(seed(force=True))
