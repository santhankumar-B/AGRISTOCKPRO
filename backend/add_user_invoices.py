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

async def insert_scanned_invoices():
    init_db()
    users = await fetch_all("SELECT * FROM users")
    if not users:
        print("No users found.")
        return

    for u in users:
        owner_id = u["id"]
        username = u["username"]
        print(f"Adding scanned paper invoices for user: {username}...")

        # 1. Supplier
        sup = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("T. STANES AND COMPANY LIMITED", owner_id))
        if not sup:
            sup_id = uid()
            await execute(
                """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sup_id, "T. STANES AND COMPANY LIMITED", "T. STANES AND COMPANY LIMITED", "6374712405", "info@tstanes.com",
                 "D.No 76/97/3-4-A Beside Hanuman Weigh Bridge, Bellary Road, Kurnool - 518003", "37AAACT7126P1ZU", 31099.00, owner_id, now_iso())
            )
        else:
            sup_id = sup["id"]
            await execute("UPDATE suppliers SET outstanding_amount = 31099.00 WHERE id = ?", (sup_id,))

        # 2. Product 1: LIQUID BIONEMATON 1 LT
        p1 = await fetch_one("SELECT * FROM products WHERE name LIKE '%BIONEMATON%' AND owner_id = ?", (owner_id,))
        if not p1:
            p1_id = uid()
            await execute(
                """INSERT INTO products (id, name, category, company, brand, barcode, current_stock, minimum_stock, unit, purchase_price, selling_price, batch_number, expiry_date, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (p1_id, "LIQUID BIONEMATON (Paecilomyces Lilacinus) 1 LT", "Bio-Pesticides", "T. STANES AND COMPANY LIMITED", "T. STANES",
                 "8903031032201", 40.0, 5.0, "LTR", 272.20, 310.00, "BN062604", "2027-06-24", owner_id, now_iso())
            )
        else:
            p1_id = p1["id"]

        # 3. Product 2: ADDON (NPK-19-19-19) 25KG
        p2 = await fetch_one("SELECT * FROM products WHERE name LIKE '%ADDON%' AND owner_id = ?", (owner_id,))
        if not p2:
            p2_id = uid()
            await execute(
                """INSERT INTO products (id, name, category, company, brand, barcode, current_stock, minimum_stock, unit, purchase_price, selling_price, batch_number, expiry_date, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (p2_id, "ADDON (NPK-19-19-19) 25KG", "Fertilizers", "T. STANES AND COMPANY LIMITED", "T. STANES",
                 "8903031012200", 5.0, 1.0, "Bag", 3045.00, 3105.00, "1919190426", "2030-04-29", owner_id, now_iso())
            )
        else:
            p2_id = p2["id"]

        # 4. Product 3: HUGO (POTASSIUM NITRATE) 1KG
        p3 = await fetch_one("SELECT * FROM products WHERE name LIKE '%HUGO%' AND owner_id = ?", (owner_id,))
        if not p3:
            p3_id = uid()
            await execute(
                """INSERT INTO products (id, name, category, company, brand, barcode, current_stock, minimum_stock, unit, purchase_price, selling_price, batch_number, expiry_date, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (p3_id, "HUGO (POTASSIUM NITRATE) 1KG", "Fertilizers", "T. STANES AND COMPANY LIMITED", "T. STANES",
                 "8903031012201", 25.0, 5.0, "Packet", 142.60, 165.00, "TS/PN/0426", "2030-04-29", owner_id, now_iso())
            )
        else:
            p3_id = p3["id"]

        # 5. Purchase Invoice 1: 303103220172
        inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303103220172", owner_id))
        items1 = [{
            "product_id": p1_id,
            "product_name": "LIQUID BIONEMATON (Paecilomyces Lilacinus) 1 LT",
            "unit": "LTR",
            "qty": 40.0,
            "unit_price": 272.20,
            "amount": 10888.00,
            "batch_number": "BN062604",
            "expiry_date": "2027-06-24"
        }]
        if not inv1:
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303103220172", "2026-07-06", "Main Warehouse", "Direct Road", "Credit", "2026-07-06",
                 "Scanned Tax Invoice 303103220172", json.dumps(items1), 14400.00, 3512.00, 272.20, 272.20, 11432.00, 0.0, 11432.00, "Credit", "posted", owner_id, now_iso())
            )

        # 6. Purchase Invoice 2: 303101220021
        inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303101220021", owner_id))
        items2 = [
            {
                "product_id": p2_id,
                "product_name": "ADDON (NPK-19-19-19) 25KG",
                "unit": "Bag",
                "qty": 5.0,
                "unit_price": 3045.00,
                "amount": 15225.00,
                "batch_number": "1919190426",
                "expiry_date": "2030-04-29"
            },
            {
                "product_id": p3_id,
                "product_name": "HUGO (POTASSIUM NITRATE) 1KG",
                "unit": "Packet",
                "qty": 25.0,
                "unit_price": 142.60,
                "amount": 3565.00,
                "batch_number": "TS/PN/0426",
                "expiry_date": "2030-04-29"
            }
        ]
        if not inv2:
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303101220021", "2026-04-30", "Main Warehouse", "Direct Road", "Credit", "2026-04-30",
                 "Scanned Tax Invoice 303101220021", json.dumps(items2), 24500.00, 5770.00, 468.26, 468.26, 19667.00, 0.0, 19667.00, "Credit", "posted", owner_id, now_iso())
            )

    print("Scanned paper invoices successfully inserted into database!")

if __name__ == "__main__":
    asyncio.run(insert_scanned_invoices())
