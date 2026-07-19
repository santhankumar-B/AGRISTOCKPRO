import asyncio
import os
import sys
import uuid
import json
from datetime import datetime, timezone

sys.path.append(os.path.dirname(__file__))
from database import init_db, fetch_one, fetch_all, execute

def uid():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

async def insert_invoice_3():
    init_db()
    users = await fetch_all("SELECT * FROM users")
    if not users:
        print("No users found.")
        return

    for u in users:
        owner_id = u["id"]
        username = u["username"]
        print(f"Adding Scanned Invoice #303101220019 for user: {username}...")

        # 1. Supplier: T. STANES AND COMPANY LIMITED
        sup = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("T. STANES AND COMPANY LIMITED", owner_id))
        if not sup:
            sup_id = uid()
            await execute(
                """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sup_id, "T. STANES AND COMPANY LIMITED", "T. STANES AND COMPANY LIMITED", "6374712405", "info@tstanes.com",
                 "D.NO 76/97/3-4-A BESIDE HANUMAN WEIGH BRIDGE, BELLARY ROAD, KURNOOL, PinCode: 518003", "37AAACT7126P1ZU", 67419.00, owner_id, now_iso())
            )
        else:
            sup_id = sup["id"]
            await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 36320.00 WHERE id = ?", (sup_id,))

        # 2. Product 1: TAKEON - (MONO POTASSIUM PHOSPHATE) 25KG
        p1 = await fetch_one("SELECT * FROM products WHERE name LIKE '%TAKEON%' AND owner_id = ?", (owner_id,))
        if not p1:
            p1_id = uid()
            await execute(
                """INSERT INTO products (id, name, category, company, brand, barcode, current_stock, minimum_stock, unit, purchase_price, selling_price, batch_number, expiry_date, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (p1_id, "TAKEON (MONO POTASSIUM PHOSPHATE) 25KG", "Fertilizers", "T. STANES AND COMPANY LIMITED", "T. STANES",
                 "31056000", 5.0, 1.0, "Bag", 5138.00, 5250.00, "TS/MKP0426", "2030-04-29", owner_id, now_iso())
            )
        else:
            p1_id = p1["id"]
            await execute("UPDATE products SET current_stock = current_stock + 5.0 WHERE id = ?", (p1_id,))

        # 3. Product 2: PROPLUS - (CALCIUM NITRATE) 25KG
        p2 = await fetch_one("SELECT * FROM products WHERE name LIKE '%PROPLUS%' AND owner_id = ?", (owner_id,))
        if not p2:
            p2_id = uid()
            await execute(
                """INSERT INTO products (id, name, category, company, brand, barcode, current_stock, minimum_stock, unit, purchase_price, selling_price, batch_number, expiry_date, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (p2_id, "PROPLUS (CALCIUM NITRATE) 25KG", "Fertilizers", "T. STANES AND COMPANY LIMITED", "T. STANES",
                 "31029090", 5.0, 1.0, "Bag", 1780.00, 1850.00, "TS/CN/0426", "2030-04-29", owner_id, now_iso())
            )
        else:
            p2_id = p2["id"]
            await execute("UPDATE products SET current_stock = current_stock + 5.0 WHERE id = ?", (p2_id,))

        # 4. Purchase Invoice 3: 303101220019
        inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303101220019", owner_id))
        items3 = [
            {
                "product_id": p1_id,
                "product_name": "TAKEON (MONO POTASSIUM PHOSPHATE) 25KG",
                "unit": "Bag",
                "qty": 5.0,
                "unit_price": 5138.00,
                "amount": 25690.00,
                "batch_number": "TS/MKP0426",
                "expiry_date": "2030-04-29"
            },
            {
                "product_id": p2_id,
                "product_name": "PROPLUS (CALCIUM NITRATE) 25KG",
                "unit": "Bag",
                "qty": 5.0,
                "unit_price": 1780.00,
                "amount": 8900.00,
                "batch_number": "TS/CN/0426",
                "expiry_date": "2030-04-29"
            }
        ]
        if not inv3:
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303101220019", "2026-06-25", "Main Warehouse", "O/NANDESWARA", "Credit", "2026-06-25",
                 "Scanned Tax Invoice 303101220019", json.dumps(items3), 45125.00, 10535.00, 864.75, 864.75, 36320.00, 0.0, 36320.00, "Credit", "posted", owner_id, now_iso())
            )

    print("Scanned Invoice #303101220019 successfully inserted into database!")

if __name__ == "__main__":
    asyncio.run(insert_invoice_3())
