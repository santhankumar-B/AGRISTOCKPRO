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

async def insert_5_new_july21_set2_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding 5 New Invoices (July 21 Set 2) for ADMIN user ({owner_id})...")

    # Supplier 1: NEW INDIA CROP SCIENCE
    sup_nics = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("NEW INDIA CROP SCIENCE", owner_id))
    if not sup_nics:
        sup_nics_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_nics_id, "NEW INDIA CROP SCIENCE", "NEW INDIA CROP SCIENCE", "9703835362", "info@newindiacropscience.com",
             "D.No 17-01-272-03, Godown 4, Rapthadu, Anantapuramu - 515002 AP", "37AWWPB6419N1ZS", 108780.00, owner_id, now_iso())
        )
    else:
        sup_nics_id = sup_nics["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 108780.00 WHERE id = ?", (sup_nics_id,))

    # Supplier 2: NOVA AGRI SCIENCES PVT LTD
    sup_nova_sci = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("NOVA AGRI SCIENCES PVT LTD", owner_id))
    if not sup_nova_sci:
        sup_nova_sci_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_nova_sci_id, "NOVA AGRI SCIENCES PVT LTD", "NOVA AGRI SCIENCES PVT LTD", "7995084789", "accounts@novaagri.in",
             "Sy No 251/A1, Baswapur Road, Singannaguda TG - 502279", "36AADCN9236F2ZC", 99538.73, owner_id, now_iso())
        )
    else:
        sup_nova_sci_id = sup_nova_sci["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 99538.73 WHERE id = ?", (sup_nova_sci_id,))

    # Supplier 3: NOVA AGRITECH LIMITED
    sup_nova_tech = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("NOVA AGRITECH LIMITED", owner_id))
    if not sup_nova_tech:
        sup_nova_tech_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_nova_tech_id, "NOVA AGRITECH LIMITED", "NOVA AGRITECH LIMITED", "7995084789", "accounts@novaagri.in",
             "Sy No 251/A, Singannaguda Village, Mulugu Mandal Siddipet, TG - 502279", "36AACCN8771A2ZH", 14750.91, owner_id, now_iso())
        )
    else:
        sup_nova_tech_id = sup_nova_tech["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 14750.91 WHERE id = ?", (sup_nova_tech_id,))

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
             f"89030403{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- 1. NEW INDIA CROP SCIENCE: NICS/25-26/685 (16-03-2026) ----------------
    p_min19 = await get_or_create_prod("MINERVA 19:19:19 25KG BAG", "Fertilizers", "Bag", 1701.00, 1850.00, "MIN191919", "2028-03-16", "NEW INDIA CROP SCIENCE")
    p_min20 = await get_or_create_prod("MINERVA 20:20:20 25KG BAG", "Fertilizers", "Bag", 1911.00, 2050.00, "MIN202020", "2028-03-16", "NEW INDIA CROP SCIENCE")
    p_min12 = await get_or_create_prod("MINERVA 12:61:00 25KG BAG", "Fertilizers", "Bag", 2310.00, 2500.00, "MIN126100", "2028-03-16", "NEW INDIA CROP SCIENCE")
    p_min00 = await get_or_create_prod("MINERVA 00:52:34 25KG BAG", "Fertilizers", "Bag", 3003.00, 3200.00, "MIN005234", "2028-03-16", "NEW INDIA CROP SCIENCE")
    p_min13_00 = await get_or_create_prod("MINERVA 13-00-45 25KG BAG", "Fertilizers", "Bag", 2205.00, 2400.00, "MIN130045", "2028-03-16", "NEW INDIA CROP SCIENCE")

    await execute("UPDATE products SET current_stock = current_stock + 15 WHERE id = ?", (p_min19,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_min20,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_min12,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_min00,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_min13_00,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("NICS/25-26/685", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_min19, "product_name": "MINERVA 19:19:19 25KG BAG", "unit": "Bag", "qty": 15.0, "unit_price": 1620.00, "amount": 24300.00, "batch_number": "MIN191919", "expiry_date": "2028-03-16"},
            {"product_id": p_min20, "product_name": "MINERVA 20:20:20 25KG BAG", "unit": "Bag", "qty": 10.0, "unit_price": 1820.00, "amount": 18200.00, "batch_number": "MIN202020", "expiry_date": "2028-03-16"},
            {"product_id": p_min12, "product_name": "MINERVA 12:61:00 25KG BAG", "unit": "Bag", "qty": 10.0, "unit_price": 2200.00, "amount": 22000.00, "batch_number": "MIN126100", "expiry_date": "2028-03-16"},
            {"product_id": p_min00, "product_name": "MINERVA 00:52:34 25KG BAG", "unit": "Bag", "qty": 10.0, "unit_price": 2860.00, "amount": 28600.00, "batch_number": "MIN005234", "expiry_date": "2028-03-16"},
            {"product_id": p_min13_00, "product_name": "MINERVA 13-00-45 25KG BAG", "unit": "Bag", "qty": 5.0, "unit_price": 2100.00, "amount": 10500.00, "batch_number": "MIN130045", "expiry_date": "2028-03-16"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nics_id, "NEW INDIA CROP SCIENCE", "NICS/25-26/685", "2026-03-16", "Main Warehouse", "Direct", "Credit", "2026-03-16",
             "Scanned NICS Invoice NICS/25-26/685", json.dumps(items1), 103600.00, 0.0, 2590.00, 2590.00, 108780.00, 0.0, 108780.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 2. NOVA AGRI SCIENCES: 226273600428 (25-05-2026) ----------------
    p_novasweep5 = await get_or_create_prod("Novasupersweeper-5 L", "Pesticides", "Can", 1850.11, 2050.00, "1195", "2028-05-21", "NOVA AGRI SCIENCES")
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_novasweep5,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("226273600428", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_novasweep5, "product_name": "Novasupersweeper-5 L", "unit": "Can", "qty": 40.0, "unit_price": 1567.89, "amount": 62715.57, "batch_number": "1195", "expiry_date": "2028-05-21"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_sci_id, "NOVA AGRI SCIENCES PVT LTD", "226273600428", "2026-05-25", "Main Warehouse", "Mangala Goods", "Credit", "2026-05-25",
             "Scanned Nova Invoice 226273600428", json.dumps(items2), 62715.57, 0.0, 5644.40, 5644.40, 74004.37, 0.0, 74004.37, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 3. NOVA AGRI SCIENCES: 226273600042 (10-04-2026) ----------------
    p_farmzyme1 = await get_or_create_prod("Farm Zyme-1 L", "Bio-Fertilizers", "Bottle", 327.66, 380.00, "1125", "2028-09-26", "NOVA AGRI SCIENCES")
    p_farmzyme500 = await get_or_create_prod("Farm Zyme 500 ML", "Bio-Fertilizers", "Bottle", 175.33, 200.00, "1117", "2028-01-20", "NOVA AGRI SCIENCES")

    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_farmzyme1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_farmzyme500,))

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("226273600042", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_farmzyme1, "product_name": "Farm Zyme-1 L", "unit": "Bottle", "qty": 10.0, "unit_price": 312.06, "amount": 3120.58, "batch_number": "1125", "expiry_date": "2028-09-26"},
            {"product_id": p_farmzyme500, "product_name": "Farm Zyme 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 166.98, "amount": 3339.57, "batch_number": "1117", "expiry_date": "2028-01-20"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_sci_id, "NOVA AGRI SCIENCES PVT LTD", "226273600042", "2026-04-10", "Main Warehouse", "Mangala Goods", "Credit", "2026-04-10",
             "Scanned Nova Invoice 226273600042", json.dumps(items3), 6460.15, 0.0, 161.51, 161.51, 6783.16, 0.0, 6783.16, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 4. NOVA AGRITECH: 126273600358 (30-05-2026) ----------------
    p_novaboron5 = await get_or_create_prod("Nova Boron 20%-5 Kg", "Fertilizers", "Bucket", 1475.09, 1650.00, "N26004", "2029-05-20", "NOVA AGRITECH LIMITED")
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_novaboron5,))

    inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("126273600358", owner_id))
    if not inv4:
        items4 = [
            {"product_id": p_novaboron5, "product_name": "Nova Boron 20%-5 Kg", "unit": "Bucket", "qty": 10.0, "unit_price": 1404.85, "amount": 14048.49, "batch_number": "N26004", "expiry_date": "2029-05-20"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_tech_id, "NOVA AGRITECH LIMITED", "126273600358", "2026-05-30", "Main Warehouse", "Mangala Goods", "Credit", "2026-05-30",
             "Scanned Nova Invoice 126273600358", json.dumps(items4), 14048.49, 0.0, 351.21, 351.21, 14750.91, 0.0, 14750.91, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 5. NOVA AGRI SCIENCES: 226273600033 (09-04-2026) ----------------
    p_novasweep1 = await get_or_create_prod("Novasupersweeper-1 L", "Pesticides", "Bottle", 375.02, 420.00, "1178", "2028-03-30", "NOVA AGRI SCIENCES")
    await execute("UPDATE products SET current_stock = current_stock + 50 WHERE id = ?", (p_novasweep1,))

    inv5 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("226273600033", owner_id))
    if not inv5:
        items5 = [
            {"product_id": p_novasweep1, "product_name": "Novasupersweeper-1 L", "unit": "Bottle", "qty": 50.0, "unit_price": 317.82, "amount": 15890.85, "batch_number": "1178", "expiry_date": "2028-03-30"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_sci_id, "NOVA AGRI SCIENCES PVT LTD", "226273600033", "2026-04-09", "Main Warehouse", "Mangala Goods", "Credit", "2026-04-09",
             "Scanned Nova Invoice 226273600033", json.dumps(items5), 15890.85, 0.0, 1430.18, 1430.18, 18751.20, 0.0, 18751.20, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added 5 New Invoices (July 21 Set 2) into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_5_new_july21_set2_admin())
