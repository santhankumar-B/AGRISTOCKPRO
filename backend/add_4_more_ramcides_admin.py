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

async def insert_4_more_ramcides_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding 3 More Ramcides CropScience Invoices for ADMIN user ({owner_id})...")

    # 2. Get or create Supplier: Ramcides CropScience Pvt. Ltd.
    sup = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("Ramcides CropScience Pvt. Ltd.", owner_id))
    if not sup:
        sup_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_id, "Ramcides CropScience Pvt. Ltd.", "Ramcides CropScience Pvt. Ltd.", "9154085140", "info@ramcides.com",
             "D.No. 79/97/30-1-A, Survey No.330, KMR Godowns, Bellary Road, Kurnool - 518003 AP", "37AAACS3784N2ZQ", 425404.92, owner_id, now_iso())
        )
    else:
        sup_id = sup["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 224568.50 WHERE id = ?", (sup_id,))

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

    # ---------------- INVOICE 1: KUR/2627/0222 (28/05/2026) ----------------
    p_tribloom1 = await get_or_create_prod("Ramcides TriBloom 1 kg", "Bio-Fertilizers", "Packet", 1253.70, 1350.00, "RCSP022601", "2031-02-26")
    p_tribloom500 = await get_or_create_prod("Ramcides TriBloom 500 gm", "Bio-Fertilizers", "Packet", 632.10, 700.00, "RCSP022601", "2031-02-26")

    await execute("UPDATE products SET current_stock = current_stock + 70 WHERE id = ?", (p_tribloom1,))
    await execute("UPDATE products SET current_stock = current_stock + 60 WHERE id = ?", (p_tribloom500,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("KUR/2627/0222", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_tribloom1, "product_name": "Ramcides TriBloom 1 kg", "unit": "Packet", "qty": 70.0, "unit_price": 1194.00, "amount": 83580.00, "batch_number": "RCSP022601", "expiry_date": "2031-02-26"},
            {"product_id": p_tribloom500, "product_name": "Ramcides TriBloom 500 gm", "unit": "Packet", "qty": 60.0, "unit_price": 602.00, "amount": 36120.00, "batch_number": "RCSP022601", "expiry_date": "2031-02-26"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_id, "Ramcides CropScience Pvt. Ltd.", "KUR/2627/0222", "2026-05-28", "Main Warehouse", "Direct", "Credit", "2026-05-28",
             "Scanned Ramcides Invoice KUR/2627/0222", json.dumps(items1), 119700.00, 0.0, 2992.50, 2992.50, 125685.00, 0.0, 125685.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 2: KUR/2627/0225 (29/05/2026) ----------------
    p_trum500 = await get_or_create_prod("Trumpet 500 gm", "Fungicides", "Packet", 647.09, 720.00, "RCSP102501", "2027-10-10")
    p_medusa250 = await get_or_create_prod("Medusa 250 gm", "Pesticides", "Packet", 400.61, 450.00, "RCSJ092514", "2027-09-14")
    p_thene100 = await get_or_create_prod("Thene 100 gm", "Pesticides", "Packet", 72.33, 85.00, "RCSJ022672", "2028-02-20")
    p_mashoor500 = await get_or_create_prod("Mashoor 500 gm", "Pesticides", "Packet", 402.97, 460.00, "RCSP092501", "2027-09-10")
    p_tol500 = await get_or_create_prod("Tolwin 500 ml", "Pesticides", "Bottle", 832.49, 900.00, "RCSP092501", "2027-09-10")
    p_tol250 = await get_or_create_prod("Tolwin 250 ml", "Pesticides", "Bottle", 422.15, 460.00, "RCSP082502", "2027-08-19")
    p_fungy500 = await get_or_create_prod("Fungy 500 gm", "Fungicides", "Packet", 284.97, 320.00, "RCSP092501", "2027-09-10")

    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_trum500,))
    await execute("UPDATE products SET current_stock = current_stock + 16 WHERE id = ?", (p_medusa250,))
    await execute("UPDATE products SET current_stock = current_stock + 60 WHERE id = ?", (p_thene100,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_mashoor500,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_tol500,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_tol250,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_fungy500,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("KUR/2627/0225", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_trum500, "product_name": "Trumpet 500 gm", "unit": "Packet", "qty": 20.0, "unit_price": 548.38, "amount": 10897.50, "batch_number": "RCSP102501", "expiry_date": "2027-10-10"},
            {"product_id": p_medusa250, "product_name": "Medusa 250 gm", "unit": "Packet", "qty": 16.0, "unit_price": 339.50, "amount": 5432.00, "batch_number": "RCSJ092514", "expiry_date": "2027-09-14"},
            {"product_id": p_thene100, "product_name": "Thene 100 gm", "unit": "Packet", "qty": 60.0, "unit_price": 61.30, "amount": 3678.00, "batch_number": "RCSJ022672", "expiry_date": "2028-02-20"},
            {"product_id": p_mashoor500, "product_name": "Mashoor 500 gm", "unit": "Packet", "qty": 20.0, "unit_price": 341.50, "amount": 6830.00, "batch_number": "RCSP092501", "expiry_date": "2027-09-10"},
            {"product_id": p_tol500, "product_name": "Tolwin 500 ml", "unit": "Bottle", "qty": 20.0, "unit_price": 705.50, "amount": 14110.00, "batch_number": "RCSP092501", "expiry_date": "2027-09-10"},
            {"product_id": p_tol250, "product_name": "Tolwin 250 ml", "unit": "Bottle", "qty": 40.0, "unit_price": 357.75, "amount": 14310.00, "batch_number": "RCSP082502", "expiry_date": "2027-08-19"},
            {"product_id": p_fungy500, "product_name": "Fungy 500 gm", "unit": "Packet", "qty": 20.0, "unit_price": 241.50, "amount": 4830.00, "batch_number": "RCSP092501", "expiry_date": "2027-09-10"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_id, "Ramcides CropScience Pvt. Ltd.", "KUR/2627/0225", "2026-05-29", "Main Warehouse", "Direct", "Credit", "2026-05-29",
             "Scanned Ramcides Invoice KUR/2627/0225", json.dumps(items2), 60087.50, 0.0, 3564.00, 3564.00, 67215.50, 0.0, 67215.50, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 3: KUR/2627/0223 (29/05/2026) ----------------
    p_vesomax1 = await get_or_create_prod("VesoMax 1 Ltr", "Bio-Fertilizers", "Bottle", 760.20, 840.00, "RCSP012601", "2029-01-27")
    p_vesomax500 = await get_or_create_prod("VesoMax 500 ml", "Bio-Fertilizers", "Bottle", 401.10, 450.00, "RCSP012601", "2029-01-27")
    p_vesol1 = await get_or_create_prod("Vesol 1 Ltr", "Bio-Fertilizers", "Bottle", 781.20, 860.00, "RCSP082501", "2028-08-11")
    p_vesol500 = await get_or_create_prod("Vesol 500 ml", "Bio-Fertilizers", "Bottle", 411.60, 460.00, "RCSP072402", "2026-07-25")

    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_vesomax1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_vesomax500,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_vesol1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_vesol500,))

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("KUR/2627/0223", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_vesomax1, "product_name": "VesoMax 1 Ltr", "unit": "Bottle", "qty": 10.0, "unit_price": 724.00, "amount": 7240.00, "batch_number": "RCSP012601", "expiry_date": "2029-01-27"},
            {"product_id": p_vesomax500, "product_name": "VesoMax 500 ml", "unit": "Bottle", "qty": 20.0, "unit_price": 382.00, "amount": 7640.00, "batch_number": "RCSP012601", "expiry_date": "2029-01-27"},
            {"product_id": p_vesol1, "product_name": "Vesol 1 Ltr", "unit": "Bottle", "qty": 10.0, "unit_price": 744.00, "amount": 7440.00, "batch_number": "RCSP082501", "expiry_date": "2028-08-11"},
            {"product_id": p_vesol500, "product_name": "Vesol 500 ml", "unit": "Bottle", "qty": 20.0, "unit_price": 392.00, "amount": 7840.00, "batch_number": "RCSP072402", "expiry_date": "2026-07-25"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_id, "Ramcides CropScience Pvt. Ltd.", "KUR/2627/0223", "2026-05-29", "Main Warehouse", "Direct", "Credit", "2026-05-29",
             "Scanned Ramcides Invoice KUR/2627/0223", json.dumps(items3), 30160.00, 0.0, 754.00, 754.00, 31668.00, 0.0, 31668.00, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added 3 More Ramcides CropScience invoices into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_4_more_ramcides_admin())
