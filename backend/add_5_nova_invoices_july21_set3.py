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

async def insert_5_nova_july21_set3_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding 5 Nova Invoices (July 21 Set 3) for ADMIN user ({owner_id})...")

    # Supplier 1: NOVA AGRI SCIENCES PVT LTD
    sup_nova_sci = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("NOVA AGRI SCIENCES PVT LTD", owner_id))
    if not sup_nova_sci:
        sup_nova_sci_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_nova_sci_id, "NOVA AGRI SCIENCES PVT LTD", "NOVA AGRI SCIENCES PVT LTD", "7995084789", "accounts@novaagri.in",
             "Sy No 251/A1, Baswapur Road, Singannaguda TG - 502279", "36AADCN9236F2ZC", 20802.32, owner_id, now_iso())
        )
    else:
        sup_nova_sci_id = sup_nova_sci["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 20802.32 WHERE id = ?", (sup_nova_sci_id,))

    # Supplier 2: NOVA AGRITECH LIMITED
    sup_nova_tech = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("NOVA AGRITECH LIMITED", owner_id))
    if not sup_nova_tech:
        sup_nova_tech_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_nova_tech_id, "NOVA AGRITECH LIMITED", "NOVA AGRITECH LIMITED", "7995084789", "accounts@novaagri.in",
             "Sy No 251/A, Singannaguda Village, Mulugu Mandal Siddipet, TG - 502279", "36AACCN8771A2ZH", 105313.99, owner_id, now_iso())
        )
    else:
        sup_nova_tech_id = sup_nova_tech["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 105313.99 WHERE id = ?", (sup_nova_tech_id,))

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
             f"89030404{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- 1. NOVA AGRITECH: 126273600139 (11-05-2026) ----------------
    p_snip250 = await get_or_create_prod("Sniper-250 ML", "Pesticides", "Bottle", 452.21, 510.00, "N26020", "2029-02-19", "NOVA AGRITECH LIMITED")
    p_snip500 = await get_or_create_prod("Sniper-500 ML", "Pesticides", "Bottle", 839.82, 950.00, "N26001", "2029-04-28", "NOVA AGRITECH LIMITED")

    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_snip250,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_snip500,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("126273600139", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_snip250, "product_name": "Sniper-250 ML", "unit": "Bottle", "qty": 40.0, "unit_price": 430.67, "amount": 17226.96, "batch_number": "N26020", "expiry_date": "2029-02-19"},
            {"product_id": p_snip500, "product_name": "Sniper-500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 799.83, "amount": 15996.50, "batch_number": "N26001", "expiry_date": "2029-04-28"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_tech_id, "NOVA AGRITECH LIMITED", "126273600139", "2026-05-11", "Main Warehouse", "Mangala Goods", "Credit", "2026-05-11",
             "Scanned Nova Invoice 126273600139", json.dumps(items1), 33223.46, 0.0, 830.58, 830.58, 34884.63, 0.0, 34884.63, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 2. NOVA AGRITECH: 126273601342 (02-07-2026) ----------------
    p_nova2828 = await get_or_create_prod("Nova Fert 2828 25 Kg", "Fertilizers", "Bag", 3725.23, 4100.00, "N26004", "2029-06-05", "NOVA AGRITECH LIMITED")
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_nova2828,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("126273601342", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_nova2828, "product_name": "Nova Fert 2828 25 Kg", "unit": "Bag", "qty": 10.0, "unit_price": 3547.84, "amount": 35478.35, "batch_number": "N26004", "expiry_date": "2029-06-05"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_tech_id, "NOVA AGRITECH LIMITED", "126273601342", "2026-07-02", "Main Warehouse", "Mangala Goods", "Credit", "2026-07-02",
             "Scanned Nova Invoice 126273601342", json.dumps(items2), 35478.35, 0.0, 886.96, 886.96, 37252.27, 0.0, 37252.27, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 3. NOVA AGRI SCIENCES: 226273600240 (11-05-2026) ----------------
    p_panth250 = await get_or_create_prod("Nova Panther-250 ML", "Pesticides", "Bottle", 96.26, 115.00, "1046", "2028-01-28", "NOVA AGRI SCIENCES")
    p_panth500 = await get_or_create_prod("Nova Panther-500 ML", "Pesticides", "Bottle", 172.51, 200.00, "1046", "2028-01-28", "NOVA AGRI SCIENCES")

    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_panth250,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_panth500,))

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("226273600240", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_panth250, "product_name": "Nova Panther-250 ML", "unit": "Bottle", "qty": 40.0, "unit_price": 81.58, "amount": 3263.02, "batch_number": "1046", "expiry_date": "2028-01-28"},
            {"product_id": p_panth500, "product_name": "Nova Panther-500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 146.20, "amount": 2923.95, "batch_number": "1046", "expiry_date": "2028-01-28"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_sci_id, "NOVA AGRI SCIENCES PVT LTD", "226273600240", "2026-05-11", "Main Warehouse", "Mangala Goods", "Credit", "2026-05-11",
             "Scanned Nova Invoice 226273600240", json.dumps(items3), 6186.97, 0.0, 556.83, 556.83, 7300.62, 0.0, 7300.62, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 4. NOVA AGRI SCIENCES: 226273600074 (17-04-2026) ----------------
    p_double100 = await get_or_create_prod("Double Action F2-100 ML", "Pesticides", "Bottle", 270.03, 300.00, "1107", "2028-04-14", "NOVA AGRI SCIENCES")
    await execute("UPDATE products SET current_stock = current_stock + 50 WHERE id = ?", (p_double100,))

    inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("226273600074", owner_id))
    if not inv4:
        items4 = [
            {"product_id": p_double100, "product_name": "Double Action F2-100 ML", "unit": "Bottle", "qty": 50.0, "unit_price": 228.84, "amount": 11442.12, "batch_number": "1107", "expiry_date": "2028-04-14"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_sci_id, "NOVA AGRI SCIENCES PVT LTD", "226273600074", "2026-04-17", "Main Warehouse", "Mangala Goods", "Credit", "2026-04-17",
             "Scanned Nova Invoice 226273600074", json.dumps(items4), 11442.12, 0.0, 1029.79, 1029.79, 13501.70, 0.0, 13501.70, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 5. NOVA AGRITECH: 126273600353 (30-05-2026) ----------------
    p_novabor1 = await get_or_create_prod("Nova Boron 20%-1 Kg", "Fertilizers", "Packet", 300.02, 340.00, "N26003", "2029-05-10", "NOVA AGRITECH LIMITED")
    p_nova0050 = await get_or_create_prod("Nova Fert 0-0-50-25 Kg", "Fertilizers", "Bag", 3325.20, 3650.00, "N26001", "2029-04-05", "NOVA AGRITECH LIMITED")
    p_novagoog10 = await get_or_create_prod("Nova Googley-10 Kg", "Fertilizers", "Bag", 1510.09, 1700.00, "202603LSNF06", "2029-05-07", "NOVA AGRITECH LIMITED")

    await execute("UPDATE products SET current_stock = current_stock + 30 WHERE id = ?", (p_novabor1,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_nova0050,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_novagoog10,))

    inv5 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("126273600353", owner_id))
    if not inv5:
        items5 = [
            {"product_id": p_novabor1, "product_name": "Nova Boron 20%-1 Kg", "unit": "Packet", "qty": 30.0, "unit_price": 285.74, "amount": 8572.05, "batch_number": "N26003", "expiry_date": "2029-05-10"},
            {"product_id": p_nova0050, "product_name": "Nova Fert 0-0-50-25 Kg", "unit": "Bag", "qty": 5.0, "unit_price": 3166.86, "amount": 15834.29, "batch_number": "N26001", "expiry_date": "2029-04-05"},
            {"product_id": p_novagoog10, "product_name": "Nova Googley-10 Kg", "unit": "Bag", "qty": 5.0, "unit_price": 1438.18, "amount": 7190.90, "batch_number": "202603LSNF06", "expiry_date": "2029-05-07"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_tech_id, "NOVA AGRITECH LIMITED", "126273600353", "2026-05-30", "Main Warehouse", "Mangala Goods", "Credit", "2026-05-30",
             "Scanned Nova Invoice 126273600353", json.dumps(items5), 31597.24, 0.0, 789.93, 789.93, 33177.09, 0.0, 33177.09, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added 5 Nova Invoices (July 21 Set 3) into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_5_nova_july21_set3_admin())
