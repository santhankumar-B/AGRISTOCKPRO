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

async def insert_4_nova_july21_set4_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding 4 Nova Invoices (July 21 Set 4) for ADMIN user ({owner_id})...")

    # Supplier 1: NOVA AGRI SCIENCES PVT LTD
    sup_nova_sci = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("NOVA AGRI SCIENCES PVT LTD", owner_id))
    if not sup_nova_sci:
        sup_nova_sci_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_nova_sci_id, "NOVA AGRI SCIENCES PVT LTD", "NOVA AGRI SCIENCES PVT LTD", "7995084789", "accounts@novaagri.in",
             "Sy No 251/A1, Baswapur Road, Singannaguda TG - 502279", "36AADCN9236F2ZC", 146333.60, owner_id, now_iso())
        )
    else:
        sup_nova_sci_id = sup_nova_sci["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 146333.60 WHERE id = ?", (sup_nova_sci_id,))

    # Supplier 2: NOVA AGRITECH LIMITED
    sup_nova_tech = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("NOVA AGRITECH LIMITED", owner_id))
    if not sup_nova_tech:
        sup_nova_tech_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_nova_tech_id, "NOVA AGRITECH LIMITED", "NOVA AGRITECH LIMITED", "7995084789", "accounts@novaagri.in",
             "Sy No 251/A, Singannaguda Village, Mulugu Mandal Siddipet, TG - 502279", "36AACCN8771A2ZH", 15222.15, owner_id, now_iso())
        )
    else:
        sup_nova_tech_id = sup_nova_tech["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 15222.15 WHERE id = ?", (sup_nova_tech_id,))

    # Helper to get/create product for Admin
    async def get_or_create_prod(name, cat, unit, price, sell_price, batch, exp, company):
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
            (pid, name, cat, company, company.split()[0],
             f"89030405{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- 1. NOVA AGRI SCIENCES: 226273600012 (07-04-2026) ----------------
    p_trin250 = await get_or_create_prod("Tri-N-250 G", "Pesticides", "Packet", 160.01, 180.00, "1136", "2028-01-16", "NOVA AGRI SCIENCES")
    p_panth250 = await get_or_create_prod("Nova Panther-250 ML", "Pesticides", "Bottle", 96.26, 115.00, "1046", "2028-01-28", "NOVA AGRI SCIENCES")
    p_panth500 = await get_or_create_prod("Nova Panther-500 ML", "Pesticides", "Bottle", 172.51, 200.00, "1046", "2028-01-28", "NOVA AGRI SCIENCES")
    p_safec250 = await get_or_create_prod("Safectain-250 G", "Pesticides", "Packet", 322.52, 360.00, "1136", "2028-03-16", "NOVA AGRI SCIENCES")

    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_trin250,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_panth250,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_panth500,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_safec250,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("226273600012", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_trin250, "product_name": "Tri-N-250 G", "unit": "Packet", "qty": 40.0, "unit_price": 135.60, "amount": 5424.14, "batch_number": "1136", "expiry_date": "2028-01-16"},
            {"product_id": p_panth250, "product_name": "Nova Panther-250 ML", "unit": "Bottle", "qty": 40.0, "unit_price": 81.58, "amount": 3263.02, "batch_number": "1046", "expiry_date": "2028-01-28"},
            {"product_id": p_panth500, "product_name": "Nova Panther-500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 146.20, "amount": 2923.95, "batch_number": "1046", "expiry_date": "2028-01-28"},
            {"product_id": p_safec250, "product_name": "Safectain-250 G", "unit": "Packet", "qty": 40.0, "unit_price": 273.32, "amount": 10932.97, "batch_number": "1136", "expiry_date": "2028-03-16"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_sci_id, "NOVA AGRI SCIENCES PVT LTD", "226273600012", "2026-04-07", "Main Warehouse", "Mangala Goods", "Credit", "2026-04-07",
             "Scanned Nova Invoice 226273600012", json.dumps(items1), 22544.08, 0.0, 2028.97, 2028.97, 26602.01, 0.0, 26602.01, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 2. NOVA AGRI SCIENCES: 226273600043 (10-04-2026) ----------------
    p_superm50 = await get_or_create_prod("Super M-br-50 ML", "Pesticides", "Bottle", 290.71, 320.00, "1070", "2027-12-30", "NOVA AGRI SCIENCES")
    p_supsnip250 = await get_or_create_prod("Super Sniper-250 ML", "Pesticides", "Bottle", 452.21, 510.00, "1147", "2027-03-24", "NOVA AGRI SCIENCES")
    p_supsnip500 = await get_or_create_prod("Super Sniper-500 ML", "Pesticides", "Bottle", 839.82, 950.00, "1143", "2027-12-26", "NOVA AGRI SCIENCES")
    p_tgold250 = await get_or_create_prod("T-Gold S D-250 ML", "Pesticides", "Bottle", 581.41, 650.00, "1083", "2027-12-26", "NOVA AGRI SCIENCES")
    p_tgold500 = await get_or_create_prod("T-Gold S D-500 ML", "Pesticides", "Bottle", 1136.99, 1280.00, "1040", "2028-01-28", "NOVA AGRI SCIENCES")

    await execute("UPDATE products SET current_stock = current_stock + 70 WHERE id = ?", (p_superm50,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_supsnip250,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_supsnip500,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_tgold250,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_tgold500,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("226273600043", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_superm50, "product_name": "Super M-br-50 ML", "unit": "Bottle", "qty": 70.0, "unit_price": 246.36, "amount": 17245.31, "batch_number": "1070", "expiry_date": "2027-12-30"},
            {"product_id": p_supsnip250, "product_name": "Super Sniper-250 ML", "unit": "Bottle", "qty": 40.0, "unit_price": 383.23, "amount": 15329.16, "batch_number": "1147", "expiry_date": "2027-03-24"},
            {"product_id": p_supsnip500, "product_name": "Super Sniper-500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 711.71, "amount": 14234.22, "batch_number": "1143", "expiry_date": "2027-12-26"},
            {"product_id": p_tgold250, "product_name": "T-Gold S D-250 ML", "unit": "Bottle", "qty": 40.0, "unit_price": 492.72, "amount": 19708.92, "batch_number": "1083", "expiry_date": "2027-12-26"},
            {"product_id": p_tgold500, "product_name": "T-Gold S D-500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 963.55, "amount": 19270.94, "batch_number": "1040", "expiry_date": "2028-01-28"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_sci_id, "NOVA AGRI SCIENCES PVT LTD", "226273600043", "2026-04-10", "Main Warehouse", "Mangala Goods", "Credit", "2026-04-10",
             "Scanned Nova Invoice 226273600043", json.dumps(items2), 85788.55, 0.0, 7720.98, 7720.98, 101230.50, 0.0, 101230.50, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 3. NOVA AGRI SCIENCES: 226273600133 (23-04-2026) ----------------
    p_novasweep5 = await get_or_create_prod("Novasupersweeper-5 L", "Pesticides", "Can", 1850.11, 2050.00, "1179", "2028-04-21", "NOVA AGRI SCIENCES")
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_novasweep5,))

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("226273600133", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_novasweep5, "product_name": "Novasupersweeper-5 L", "unit": "Can", "qty": 10.0, "unit_price": 1567.89, "amount": 15678.89, "batch_number": "1179", "expiry_date": "2028-04-21"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_sci_id, "NOVA AGRI SCIENCES PVT LTD", "226273600133", "2026-04-23", "Main Warehouse", "Mangala Goods", "Credit", "2026-04-23",
             "Scanned Nova Invoice 226273600133", json.dumps(items3), 15678.89, 0.0, 1411.10, 1411.10, 18501.09, 0.0, 18501.09, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 4. NOVA AGRITECH: 126273600012 (14-04-2026) ----------------
    p_zir1 = await get_or_create_prod("Zirova 999-1 L", "Bio-Pesticides", "Bottle", 745.80, 840.00, "N26012", "2029-02-01", "NOVA AGRITECH LIMITED")
    p_zir500 = await get_or_create_prod("Zirova 999-500 ML", "Bio-Pesticides", "Bottle", 388.21, 440.00, "N26013", "2029-02-10", "NOVA AGRITECH LIMITED")

    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_zir1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_zir500,))

    inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("126273600012", owner_id))
    if not inv4:
        items4 = [
            {"product_id": p_zir1, "product_name": "Zirova 999-1 L", "unit": "Bottle", "qty": 10.0, "unit_price": 710.29, "amount": 7102.89, "batch_number": "N26012", "expiry_date": "2029-02-01"},
            {"product_id": p_zir500, "product_name": "Zirova 999-500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 369.72, "amount": 7394.40, "batch_number": "N26013", "expiry_date": "2029-02-10"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_tech_id, "NOVA AGRITECH LIMITED", "126273600012", "2026-04-14", "Main Warehouse", "Mangala Goods", "Credit", "2026-04-14",
             "Scanned Nova Invoice 126273600012", json.dumps(items4), 14497.29, 0.0, 362.43, 362.43, 15222.15, 0.0, 15222.15, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added 4 Nova Invoices (July 21 Set 4) into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_4_nova_july21_set4_admin())
