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

async def insert_ramcides_admin_only():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding 5 Ramcides CropScience Invoices for ADMIN user ({owner_id})...")

    # 2. Get or create Supplier: Ramcides CropScience Pvt. Ltd.
    sup = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("Ramcides CropScience Pvt. Ltd.", owner_id))
    if not sup:
        sup_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_id, "Ramcides CropScience Pvt. Ltd.", "Ramcides CropScience Pvt. Ltd.", "9154085140", "info@ramcides.com",
             "D.No. 79/97/30-1-A, Survey No.330, KMR Godowns, Bellary Road, Kurnool - 518003 AP", "37AAACS3784N2ZQ", 200841.92, owner_id, now_iso())
        )
    else:
        sup_id = sup["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 200841.92 WHERE id = ?", (sup_id,))

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
            (pid, name, cat, "Ramcides CropScience Pvt. Ltd.", "Ramcides",
             f"89030380{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- INVOICE 1: KUR/2627/0358 (13/06/2026) ----------------
    p_zolo500 = await get_or_create_prod("Zolomite 500 ml", "Pesticides", "Bottle", 545.16, 600.00, "RCSP052602", "2028-05-22")
    p_zolo250 = await get_or_create_prod("Zolomite 250 ml", "Pesticides", "Bottle", 281.43, 310.00, "RCSP052601", "2028-05-18")

    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_zolo500,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_zolo250,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("KUR/2627/0358", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_zolo500, "product_name": "Zolomite 500 ml", "unit": "Bottle", "qty": 20.0, "unit_price": 462.00, "amount": 9240.00, "batch_number": "RCSP052602", "expiry_date": "2028-05-22"},
            {"product_id": p_zolo250, "product_name": "Zolomite 250 ml", "unit": "Bottle", "qty": 40.0, "unit_price": 238.50, "amount": 9540.00, "batch_number": "RCSP052601", "expiry_date": "2028-05-18"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_id, "Ramcides CropScience Pvt. Ltd.", "KUR/2627/0358", "2026-06-13", "Main Warehouse", "Direct", "Credit", "2026-06-13",
             "Scanned Ramcides Invoice KUR/2627/0358", json.dumps(items1), 18780.00, 0.0, 1690.20, 1690.20, 22160.40, 0.0, 22160.40, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 2: KUR/2627/0385 (16/06/2026) ----------------
    p_glu5 = await get_or_create_prod("Glupost 5 ltr", "Pesticides", "Can", 2336.40, 2600.00, "RCSJ052606", "2028-05-05")
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_glu5,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("KUR/2627/0385", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_glu5, "product_name": "Glupost 5 ltr", "unit": "Can", "qty": 20.0, "unit_price": 1980.00, "amount": 39600.00, "batch_number": "RCSJ052606", "expiry_date": "2028-05-05"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_id, "Ramcides CropScience Pvt. Ltd.", "KUR/2627/0385", "2026-06-16", "Main Warehouse", "Direct", "Credit", "2026-06-16",
             "Scanned Ramcides Invoice KUR/2627/0385", json.dumps(items2), 39600.00, 0.0, 3564.00, 3564.00, 46728.00, 0.0, 46728.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 3: KUR/2627/0710 (11/07/2026) ----------------
    p_tol500 = await get_or_create_prod("Tolwin 500 ml", "Pesticides", "Bottle", 833.08, 900.00, "RCSP062601", "2028-06-24")
    p_tol250 = await get_or_create_prod("Tolwin 250 ml", "Pesticides", "Bottle", 422.44, 460.00, "RCSP062601", "2028-06-24")

    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_tol500,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_tol250,))

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("KUR/2627/0710", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_tol500, "product_name": "Tolwin 500 ml", "unit": "Bottle", "qty": 20.0, "unit_price": 706.00, "amount": 14120.00, "batch_number": "RCSP062601", "expiry_date": "2028-06-24"},
            {"product_id": p_tol250, "product_name": "Tolwin 250 ml", "unit": "Bottle", "qty": 40.0, "unit_price": 358.00, "amount": 14320.00, "batch_number": "RCSP062601", "expiry_date": "2028-06-24"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_id, "Ramcides CropScience Pvt. Ltd.", "KUR/2627/0710", "2026-07-11", "Main Warehouse", "Direct", "Credit", "2026-07-11",
             "Scanned Ramcides Invoice KUR/2627/0710", json.dumps(items3), 28440.00, 0.0, 2559.60, 2559.60, 33559.20, 0.0, 33559.20, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 4: KUR/2627/0511 (29/06/2026) ----------------
    p_trum500 = await get_or_create_prod("Trumpet 500 gm", "Fungicides", "Packet", 652.99, 720.00, "RCSP102501", "2027-10-10")
    p_trum250 = await get_or_create_prod("Trumpet 250 gm", "Fungicides", "Packet", 329.44, 370.00, "RCSP102501", "2028-01-29")
    p_tol1 = await get_or_create_prod("Tolwin 1 Lt", "Pesticides", "Bottle", 1644.92, 1800.00, "RCSP012601", "2028-01-29")
    p_riki1 = await get_or_create_prod("Rikishi 1 Lt", "Pesticides", "Bottle", 356.95, 400.00, "RCSJ062602", "2028-06-17")
    p_riki500 = await get_or_create_prod("Rikishi 500 ml", "Pesticides", "Bottle", 187.33, 210.00, "RCSJ082506", "2027-08-17")

    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_trum500,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_trum250,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_tol1,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_riki1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_riki500,))

    inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("KUR/2627/0511", owner_id))
    if not inv4:
        items4 = [
            {"product_id": p_trum500, "product_name": "Trumpet 500 gm", "unit": "Packet", "qty": 20.0, "unit_price": 553.38, "amount": 11067.50, "batch_number": "RCSP102501", "expiry_date": "2027-10-10"},
            {"product_id": p_trum250, "product_name": "Trumpet 250 gm", "unit": "Packet", "qty": 40.0, "unit_price": 279.19, "amount": 11167.50, "batch_number": "RCSP102501", "expiry_date": "2028-01-29"},
            {"product_id": p_tol1, "product_name": "Tolwin 1 Lt", "unit": "Bottle", "qty": 10.0, "unit_price": 1394.00, "amount": 13940.00, "batch_number": "RCSP012601", "expiry_date": "2028-01-29"},
            {"product_id": p_riki1, "product_name": "Rikishi 1 Lt", "unit": "Bottle", "qty": 10.0, "unit_price": 302.50, "amount": 3025.00, "batch_number": "RCSJ062602", "expiry_date": "2028-06-17"},
            {"product_id": p_riki500, "product_name": "Rikishi 500 ml", "unit": "Bottle", "qty": 20.0, "unit_price": 158.75, "amount": 3175.00, "batch_number": "RCSJ082506", "expiry_date": "2027-08-17"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_id, "Ramcides CropScience Pvt. Ltd.", "KUR/2627/0511", "2026-06-29", "Main Warehouse", "Direct", "Credit", "2026-06-29",
             "Scanned Ramcides Invoice KUR/2627/0511", json.dumps(items4), 42375.00, 0.0, 3792.16, 3792.16, 49719.32, 0.0, 49719.32, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 5: KUR/2627/0381 (15/06/2026) ----------------
    p_glu1 = await get_or_create_prod("Glupost 1 Ltr", "Pesticides", "Bottle", 484.98, 540.00, "RCSI052607", "2028-05-06")
    p_glu500 = await get_or_create_prod("Glupost 500 ml", "Pesticides", "Bottle", 251.34, 280.00, "RCSI052612", "2027-10-05")

    await execute("UPDATE products SET current_stock = current_stock + 90 WHERE id = ?", (p_glu1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_glu500,))

    inv5 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("KUR/2627/0381", owner_id))
    if not inv5:
        items5 = [
            {"product_id": p_glu1, "product_name": "Glupost 1 Ltr", "unit": "Bottle", "qty": 90.0, "unit_price": 411.00, "amount": 36990.00, "batch_number": "RCSI052607", "expiry_date": "2028-05-06"},
            {"product_id": p_glu500, "product_name": "Glupost 500 ml", "unit": "Bottle", "qty": 20.0, "unit_price": 213.00, "amount": 4260.00, "batch_number": "RCSI052612", "expiry_date": "2027-10-05"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_id, "Ramcides CropScience Pvt. Ltd.", "KUR/2627/0381", "2026-06-15", "Main Warehouse", "Direct", "Credit", "2026-06-15",
             "Scanned Ramcides Invoice KUR/2627/0381", json.dumps(items5), 41250.00, 0.0, 3712.50, 3712.50, 48675.00, 0.0, 48675.00, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added 5 Ramcides CropScience invoices into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_ramcides_admin_only())
