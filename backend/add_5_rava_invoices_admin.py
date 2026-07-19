import asyncio
import os
import sys
import uuid
import json
from datetime import datetime, timezone

sys.path.append(os.path.dirname(__file__))
from database import init_db, fetch_one, execute

def uid():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

async def insert_5_rava_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding 5 Rava Agri Chemicals Invoices for ADMIN user ({owner_id})...")

    # Supplier: RAVA AGRI CHEMICALS PVT LTD
    sup_rava = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("RAVA AGRI CHEMICALS PVT LTD", owner_id))
    if not sup_rava:
        sup_rava_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "RAVA AGRI CHEMICALS PVT LTD", "9246927366", "rac@ariesagro.com",
             "D.No:15-44, Sai Nagar Venture, Rajeev Colony, Gooty Road, Anantapuramu - 515001 AP", "37AAECR5394P1ZI", 157981.00, owner_id, now_iso())
        )
    else:
        sup_rava_id = sup_rava["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 157981.00 WHERE id = ?", (sup_rava_id,))

    # Helper to get/create product for Admin
    async def get_or_create_prod(name, cat, unit, price, sell_price, batch, exp):
        p = await fetch_one("SELECT * FROM products WHERE name = ? AND owner_id = ?", (name, owner_id))
        if p:
            await execute(
                "UPDATE products SET purchase_price = ?, selling_price = ?, batch_number = ?, expiry_date = ?, unit = ? WHERE id = ?",
                (price, sell_price, batch, exp, unit, p["id"])
            )
            return p["id"]
        pid = uid()
        await execute(
            """INSERT INTO products (id, name, category, company, brand, barcode, current_stock, minimum_stock, unit, purchase_price, selling_price, batch_number, expiry_date, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pid, name, cat, "RAVA AGRI CHEMICALS PVT LTD", "RAVA",
             f"89030398{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- INVOICE 1: F/26-27/946 (09-06-2026) ----------------
    p_mag50 = await get_or_create_prod("MAG MIX 50 KG", "Bio-Fertilizers", "Bag", 3886.94, 4200.00, "T036", "2028-05-31")
    p_mag10 = await get_or_create_prod("MAG MIX 10KG", "Bio-Fertilizers", "Bag", 918.00, 1000.00, "T030", "2028-05-31")

    await execute("UPDATE products SET current_stock = current_stock + 2 WHERE id = ?", (p_mag50,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_mag10,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("F/26-27/946", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_mag50, "product_name": "MAG MIX 50 KG", "unit": "Bag", "qty": 2.0, "unit_price": 3701.85, "amount": 7403.70, "batch_number": "T036", "expiry_date": "2028-05-31"},
            {"product_id": p_mag10, "product_name": "MAG MIX 10KG", "unit": "Bag", "qty": 5.0, "unit_price": 874.29, "amount": 4371.45, "batch_number": "T030", "expiry_date": "2028-05-31"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "F/26-27/946", "2026-06-09", "Main Warehouse", "G.VEERA", "Credit", "2026-06-09",
             "Scanned Rava Invoice F/26-27/946", json.dumps(items1), 11775.15, 2591.00, 229.61, 229.61, 9643.00, 0.0, 9643.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 2: F/26-27/947 (09-06-2026) ----------------
    p_aquacal20 = await get_or_create_prod("AQUACAL 20 Ltr", "Bio-Fertilizers", "Can", 6945.38, 7500.00, "M028", "2028-05-31")
    p_aquacal25 = await get_or_create_prod("AQUACAL 2.5 LT", "Bio-Fertilizers", "Can", 1006.41, 1120.00, "M030", "2028-05-31")

    await execute("UPDATE products SET current_stock = current_stock + 2 WHERE id = ?", (p_aquacal20,))
    await execute("UPDATE products SET current_stock = current_stock + 6 WHERE id = ?", (p_aquacal25,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("F/26-27/947", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_aquacal20, "product_name": "AQUACAL 20 Ltr", "unit": "Can", "qty": 2.0, "unit_price": 6614.65, "amount": 13229.30, "batch_number": "M028", "expiry_date": "2028-05-31"},
            {"product_id": p_aquacal25, "product_name": "AQUACAL 2.5 LT", "unit": "Can", "qty": 6.0, "unit_price": 958.49, "amount": 5750.94, "batch_number": "M030", "expiry_date": "2028-05-31"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "F/26-27/947", "2026-06-09", "Main Warehouse", "G.VEERA", "Credit", "2026-06-09",
             "Scanned Rava Invoice F/26-27/947", json.dumps(items2), 18980.24, 4175.00, 370.13, 370.13, 15546.00, 0.0, 15546.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 3: F/26-27/758 (30-05-2026) ----------------
    p_plantex13 = await get_or_create_prod("PLANTEX 13-0-45 25 Kg Bag", "Fertilizers", "Bag", 4625.91, 4950.00, "T062", "2029-03-31")
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_plantex13,))

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("F/26-27/758", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_plantex13, "product_name": "PLANTEX 13-0-45 25 Kg Bag", "unit": "Bag", "qty": 20.0, "unit_price": 4405.63, "amount": 88112.60, "batch_number": "T062", "expiry_date": "2029-03-31"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "F/26-27/758", "2026-05-30", "Main Warehouse", "G.SRINU", "Credit", "2026-05-30",
             "Scanned Rava Invoice F/26-27/758", json.dumps(items3), 88112.60, 0.0, 2202.82, 2202.82, 92518.00, 0.0, 92518.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 4: F/26-27/759 (30-05-2026) ----------------
    p_aquacal5 = await get_or_create_prod("AQUACAL 5 LT", "Bio-Fertilizers", "Can", 1887.76, 2100.00, "M022", "2028-05-31")
    p_aquacal1 = await get_or_create_prod("AQUACAL 1 LT", "Bio-Fertilizers", "Bottle", 464.85, 520.00, "M027", "2028-05-31")

    await execute("UPDATE products SET current_stock = current_stock + 4 WHERE id = ?", (p_aquacal5,))
    await execute("UPDATE products SET current_stock = current_stock + 4 WHERE id = ?", (p_aquacal20,))
    await execute("UPDATE products SET current_stock = current_stock + 12 WHERE id = ?", (p_aquacal1,))

    inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("F/26-27/759", owner_id))
    if not inv4:
        items4 = [
            {"product_id": p_aquacal5, "product_name": "AQUACAL 5 LT", "unit": "Can", "qty": 4.0, "unit_price": 1797.87, "amount": 7191.48, "batch_number": "M022", "expiry_date": "2028-05-31"},
            {"product_id": p_aquacal20, "product_name": "AQUACAL 20 Ltr", "unit": "Can", "qty": 4.0, "unit_price": 6614.65, "amount": 26458.60, "batch_number": "M028", "expiry_date": "2028-05-31"},
            {"product_id": p_aquacal1, "product_name": "AQUACAL 1 LT", "unit": "Bottle", "qty": 12.0, "unit_price": 442.71, "amount": 5312.52, "batch_number": "M027", "expiry_date": "2028-05-31"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "F/26-27/759", "2026-05-30", "Main Warehouse", "G.SRINU", "Credit", "2026-05-30",
             "Scanned Rava Invoice F/26-27/759", json.dumps(items4), 38962.60, 8571.00, 759.80, 759.80, 31911.00, 0.0, 31911.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 5: F/26-27/760 (30-05-2026) ----------------
    p_marino1 = await get_or_create_prod("MARINO 1 LT", "Bio-Fertilizers", "Bottle", 893.40, 980.00, "M001/M", "2028-04-30")
    await execute("UPDATE products SET current_stock = current_stock + 12 WHERE id = ?", (p_marino1,))

    inv5 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("F/26-27/760", owner_id))
    if not inv5:
        items5 = [
            {"product_id": p_marino1, "product_name": "MARINO 1 LT", "unit": "Bottle", "qty": 12.0, "unit_price": 850.86, "amount": 10210.32, "batch_number": "M001/M", "expiry_date": "2028-04-30"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "F/26-27/760", "2026-05-30", "Main Warehouse", "G.SRINU", "Credit", "2026-05-30",
             "Scanned Rava Invoice F/26-27/760", json.dumps(items5), 10210.32, 2246.00, 199.11, 199.11, 8363.00, 0.0, 8363.00, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added 5 Rava Agri Chemicals invoices into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_5_rava_admin())
