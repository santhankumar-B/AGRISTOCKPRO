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

async def insert_5_new_rava_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding 5 New Rava Agri Chemicals Invoices for ADMIN user ({owner_id})...")

    # Supplier: RAVA AGRI CHEMICALS PVT LTD
    sup_rava = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("RAVA AGRI CHEMICALS PVT LTD", owner_id))
    if not sup_rava:
        sup_rava_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "RAVA AGRI CHEMICALS PVT LTD", "9246927366", "rac@ariesagro.com",
             "D.No:15-44, Sai Nagar Venture, Rajeev Colony, Gooty Road, Anantapuramu - 515001 AP", "37AAECR5394P1ZI", 308372.00, owner_id, now_iso())
        )
    else:
        sup_rava_id = sup_rava["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 150372.00 WHERE id = ?", (sup_rava_id,))

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
             f"89030399{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- INVOICE 1: F/26-27/407 (12-05-2026) ----------------
    p_mag10 = await get_or_create_prod("MAG MIX 10KG", "Bio-Fertilizers", "Bag", 918.00, 1000.00, "T007", "2028-04-30")
    p_mag50 = await get_or_create_prod("MAG MIX 50 KG", "Bio-Fertilizers", "Bag", 3886.94, 4200.00, "T185", "2028-03-31")
    p_agriplus = await get_or_create_prod("AGRIPRO PLUS 1 KG", "Bio-Fertilizers", "Packet", 1402.39, 1520.00, "T001", "2029-03-31")
    p_agrimin5 = await get_or_create_prod("AGROMIN SOIL PLUS 5 KG", "Bio-Fertilizers", "Bag", 1132.29, 1250.00, "T007", "2028-04-30")
    p_agrimin10 = await get_or_create_prod("AGROMIN SOIL PLUS 10 KG", "Bio-Fertilizers", "Bag", 2201.33, 2400.00, "T001", "2028-04-30")

    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_mag10,))
    await execute("UPDATE products SET current_stock = current_stock + 2 WHERE id = ?", (p_mag50,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_agriplus,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_agrimin5,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_agrimin10,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("F/26-27/407", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_mag10, "product_name": "MAG MIX 10KG", "unit": "Bag", "qty": 5.0, "unit_price": 874.29, "amount": 4371.45, "batch_number": "T007", "expiry_date": "2028-04-30"},
            {"product_id": p_mag50, "product_name": "MAG MIX 50 KG", "unit": "Bag", "qty": 2.0, "unit_price": 3701.85, "amount": 7403.70, "batch_number": "T185", "expiry_date": "2028-03-31"},
            {"product_id": p_agriplus, "product_name": "AGRIPRO PLUS 1 KG", "unit": "Packet", "qty": 10.0, "unit_price": 1335.61, "amount": 13356.10, "batch_number": "T001", "expiry_date": "2029-03-31"},
            {"product_id": p_agrimin5, "product_name": "AGROMIN SOIL PLUS 5 KG", "unit": "Bag", "qty": 10.0, "unit_price": 1078.37, "amount": 10783.70, "batch_number": "T007", "expiry_date": "2028-04-30"},
            {"product_id": p_agrimin10, "product_name": "AGROMIN SOIL PLUS 10 KG", "unit": "Bag", "qty": 5.0, "unit_price": 2096.50, "amount": 10482.50, "batch_number": "T001", "expiry_date": "2028-04-30"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "F/26-27/407", "2026-05-12", "Main Warehouse", "ASHOK LEYLAND", "Credit", "2026-05-12",
             "Scanned Rava Invoice F/26-27/407", json.dumps(items1), 46397.45, 10207.00, 904.76, 904.76, 38000.00, 0.0, 38000.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 2: F/26-27/408 (12-05-2026) ----------------
    p_fero25 = await get_or_create_prod("FEROMAG 25 KG", "Bio-Fertilizers", "Bag", 2936.09, 3200.00, "T005", "2028-05-31")
    p_aquacal5 = await get_or_create_prod("AQUACAL 5 LT", "Bio-Fertilizers", "Can", 1887.76, 2100.00, "M016", "2028-04-30")
    p_phos500 = await get_or_create_prod("PHOSPHOCOP 500 ML", "Bio-Fertilizers", "Bottle", 651.00, 720.00, "M006", "2028-04-30")

    await execute("UPDATE products SET current_stock = current_stock + 2 WHERE id = ?", (p_fero25,))
    await execute("UPDATE products SET current_stock = current_stock + 8 WHERE id = ?", (p_aquacal5,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_phos500,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("F/26-27/408", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_fero25, "product_name": "FEROMAG 25 KG", "unit": "Bag", "qty": 2.0, "unit_price": 2796.28, "amount": 5592.56, "batch_number": "T005", "expiry_date": "2028-05-31"},
            {"product_id": p_aquacal5, "product_name": "AQUACAL 5 LT", "unit": "Can", "qty": 8.0, "unit_price": 1797.87, "amount": 14382.96, "batch_number": "M016", "expiry_date": "2028-04-30"},
            {"product_id": p_phos500, "product_name": "PHOSPHOCOP 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 620.00, "amount": 12400.00, "batch_number": "M006", "expiry_date": "2028-04-30"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "F/26-27/408", "2026-05-12", "Main Warehouse", "ASHOK LEYLAND", "Credit", "2026-05-12",
             "Scanned Rava Invoice F/26-27/408", json.dumps(items2), 32375.52, 7122.00, 631.33, 631.33, 26516.00, 0.0, 26516.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 3: F/26-27/321 (07-05-2026) ----------------
    p_kphon500 = await get_or_create_prod("K PHONIC 500 g", "Bio-Fertilizers", "Packet", 602.52, 680.00, "M001", "2028-04-30")
    p_boron1 = await get_or_create_prod("BORON-20% (F S) 1 Kg", "Bio-Fertilizers", "Packet", 667.80, 740.00, "T001", "2028-04-30")
    p_boron500 = await get_or_create_prod("BORON-20% (F S) 500g", "Bio-Fertilizers", "Packet", 338.63, 380.00, "T001", "2028-04-30")
    p_agrimax1 = await get_or_create_prod("AGROMIN-MAX(F S) 1Kg", "Bio-Fertilizers", "Packet", 553.96, 620.00, "T171", "2028-02-28")

    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_kphon500,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_boron1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_boron500,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_agrimin10,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_agrimax1,))

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("F/26-27/321", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_kphon500, "product_name": "K PHONIC 500 g", "unit": "Packet", "qty": 40.0, "unit_price": 573.83, "amount": 22953.20, "batch_number": "M001", "expiry_date": "2028-04-30"},
            {"product_id": p_boron1, "product_name": "BORON-20% (F S) 1 Kg", "unit": "Packet", "qty": 20.0, "unit_price": 636.00, "amount": 12720.00, "batch_number": "T001", "expiry_date": "2028-04-30"},
            {"product_id": p_boron500, "product_name": "BORON-20% (F S) 500g", "unit": "Packet", "qty": 20.0, "unit_price": 322.50, "amount": 6450.00, "batch_number": "T001", "expiry_date": "2028-04-30"},
            {"product_id": p_agrimin10, "product_name": "AGROMIN SOIL PLUS 10 KG", "unit": "Bag", "qty": 5.0, "unit_price": 2096.50, "amount": 10482.50, "batch_number": "T025", "expiry_date": "2028-01-31"},
            {"product_id": p_agrimax1, "product_name": "AGROMIN-MAX(F S) 1Kg", "unit": "Packet", "qty": 20.0, "unit_price": 527.58, "amount": 10551.60, "batch_number": "T171", "expiry_date": "2028-02-28"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "F/26-27/321", "2026-05-07", "Main Warehouse", "ALFA AUTO", "Credit", "2026-05-07",
             "Scanned Rava Invoice F/26-27/321", json.dumps(items3), 63157.30, 13894.00, 1231.59, 1231.59, 51726.00, 0.0, 51726.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 4: F/26-27/322 (07-05-2026) ----------------
    p_phos1 = await get_or_create_prod("PHOSPHOCOP 1 LT", "Bio-Fertilizers", "Bottle", 1267.82, 1400.00, "024", "2027-11-30")
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_phos1,))

    inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("F/26-27/322", owner_id))
    if not inv4:
        items4 = [
            {"product_id": p_phos1, "product_name": "PHOSPHOCOP 1 LT", "unit": "Bottle", "qty": 10.0, "unit_price": 1207.45, "amount": 12074.50, "batch_number": "024", "expiry_date": "2027-11-30"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "F/26-27/322", "2026-05-07", "Main Warehouse", "ALFA AUTO", "Credit", "2026-05-07",
             "Scanned Rava Invoice F/26-27/322", json.dumps(items4), 12074.50, 2656.00, 235.46, 235.46, 9889.00, 0.0, 9889.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- INVOICE 5: P/26-27/760 (07-05-2026) ----------------
    p_planto500 = await get_or_create_prod("PLANTOMYCIN(F S) 500g", "Pesticides", "Packet", 1023.29, 1150.00, "234", "2027-09-26")
    p_planto250 = await get_or_create_prod("PLANTOMYCIN(F S) 250g", "Pesticides", "Packet", 530.53, 600.00, "291", "2027-10-17")

    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_planto500,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_planto250,))

    inv5 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("P/26-27/760", owner_id))
    if not inv5:
        items5 = [
            {"product_id": p_planto500, "product_name": "PLANTOMYCIN(F S) 500g", "unit": "Packet", "qty": 20.0, "unit_price": 867.20, "amount": 17344.00, "batch_number": "234", "expiry_date": "2027-09-26"},
            {"product_id": p_planto250, "product_name": "PLANTOMYCIN(F S) 250g", "unit": "Packet", "qty": 20.0, "unit_price": 449.60, "amount": 8992.00, "batch_number": "291", "expiry_date": "2027-10-17"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "P/26-27/760", "2026-05-07", "Main Warehouse", "ALFA AUTO", "Credit", "2026-05-07",
             "Scanned Rava Invoice P/26-27/760", json.dumps(items5), 26336.00, 5793.00, 1848.87, 1848.87, 24241.00, 0.0, 24241.00, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added 5 New Rava Agri Chemicals invoices into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_5_new_rava_admin())
