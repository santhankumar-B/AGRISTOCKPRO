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

async def insert_5_new_july21_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding 5 New Invoices (July 21) for ADMIN user ({owner_id})...")

    # Supplier 1: ANU AGRITECH PRIVATE LIMITED
    sup_anu = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("ANU AGRITECH PRIVATE LIMITED", owner_id))
    if not sup_anu:
        sup_anu_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_anu_id, "ANU AGRITECH PRIVATE LIMITED", "ANU AGRITECH PRIVATE LIMITED", "8019405807", "anuagritechpvtltd@gmail.com",
             "H.No: 16-192/1, Apsara Engg Works, Bollaram Ind Area, Sangareddy, Hyd TS", "35ABDCA9590H1ZA", 39099.38, owner_id, now_iso())
        )
    else:
        sup_anu_id = sup_anu["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 39099.38 WHERE id = ?", (sup_anu_id,))

    # Supplier 2: SIRIGUPPA AGRO AGENCIES
    sup_siri = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("SIRIGUPPA AGRO AGENCIES", owner_id))
    if not sup_siri:
        sup_siri_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_siri_id, "SIRIGUPPA AGRO AGENCIES", "SPIC FERTILIZERS", "9246863863", "vjaa2@yahoo.com",
             "22-383, Gandhi Bazaar, Anantapuramu - 515001 AP", "37AFVPS8565E1ZJ", 157600.00, owner_id, now_iso())
        )
    else:
        sup_siri_id = sup_siri["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 157600.00 WHERE id = ?", (sup_siri_id,))

    # Supplier 3: SRI LAKSHMI VENKATESWARA AGRO TRADERS
    sup_slv = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("SRI LAKSHMI VENKATESWARA AGRO TRADERS", owner_id))
    if not sup_slv:
        sup_slv_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "9490583999", "slvatcv@gmail.com",
             "Sy No: 71/1-1, Beside KTR Function Hall, Gooty Road, Anantapuramu AP", "37ADHPV2108G1ZJ", 66955.00, owner_id, now_iso())
        )
    else:
        sup_slv_id = sup_slv["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 66955.00 WHERE id = ?", (sup_slv_id,))

    # Supplier 4: NEW INDIA CROP SCIENCE
    sup_nics = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("NEW INDIA CROP SCIENCE", owner_id))
    if not sup_nics:
        sup_nics_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_nics_id, "NEW INDIA CROP SCIENCE", "NEW INDIA CROP SCIENCE", "9703835362", "info@newindiacropscience.com",
             "D.No 17-01-272-03, Godown 4, Rapthadu, Anantapuramu - 515002 AP", "37AWWPB6419N1ZS", 73710.00, owner_id, now_iso())
        )
    else:
        sup_nics_id = sup_nics["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 73710.00 WHERE id = ?", (sup_nics_id,))

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
             f"89030402{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- 1. ANU AGRITECH: AA/26-27/053 (20-06-2026) ----------------
    p_npk19 = await get_or_create_prod("NPK 19:19:19 25KG", "Fertilizers", "Bag", 1811.25, 1950.00, "NPK191919", "2028-06-20", "ANU AGRITECH")
    p_bon15 = await get_or_create_prod("BONUS 15:15:30 25KG", "Fertilizers", "Bag", 2165.63, 2300.00, "BON151530", "2028-06-20", "ANU AGRITECH")
    p_bon11 = await get_or_create_prod("BONUS 11:44:11 25KG", "Fertilizers", "Bag", 2323.13, 2500.00, "BON114411", "2028-06-20", "ANU AGRITECH")
    p_bon00 = await get_or_create_prod("BONUS 00:37:37 25KG", "Fertilizers", "Bag", 2520.00, 2700.00, "BON003737", "2028-06-20", "ANU AGRITECH")

    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_npk19,))
    await execute("UPDATE products SET current_stock = current_stock + 2 WHERE id = ?", (p_bon15,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_bon11,))
    await execute("UPDATE products SET current_stock = current_stock + 2 WHERE id = ?", (p_bon00,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("AA/26-27/053", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_npk19, "product_name": "NPK 19:19:19 25KG", "unit": "Bag", "qty": 10.0, "unit_price": 1725.00, "amount": 17250.00, "batch_number": "NPK191919", "expiry_date": "2028-06-20"},
            {"product_id": p_bon15, "product_name": "BONUS 15:15:30 25KG", "unit": "Bag", "qty": 2.0, "unit_price": 2062.50, "amount": 4125.00, "batch_number": "BON151530", "expiry_date": "2028-06-20"},
            {"product_id": p_bon11, "product_name": "BONUS 11:44:11 25KG", "unit": "Bag", "qty": 5.0, "unit_price": 2212.50, "amount": 11062.50, "batch_number": "BON114411", "expiry_date": "2028-06-20"},
            {"product_id": p_bon00, "product_name": "BONUS 00:37:37 25KG", "unit": "Bag", "qty": 2.0, "unit_price": 2400.00, "amount": 4800.00, "batch_number": "BON003737", "expiry_date": "2028-06-20"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_anu_id, "ANU AGRITECH PRIVATE LIMITED", "AA/26-27/053", "2026-06-20", "Main Warehouse", "ROAD", "Advance", "2026-06-20",
             "Scanned Anu Agritech Invoice AA/26-27/053", json.dumps(items1), 37237.50, 0.0, 930.94, 930.94, 39099.38, 0.0, 39099.38, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 2. SIRIGUPPA AGRO: SAA-271 (22-04-2026) ----------------
    p_spic_cms = await get_or_create_prod("SPIC CMS PRO 50 KG", "Fertilizers", "Bag", 530.00, 580.00, "CMSPRO50", "2028-04-22", "SIRIGUPPA AGRO")
    await execute("UPDATE products SET current_stock = current_stock + 160 WHERE id = ?", (p_spic_cms,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SAA-271", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_spic_cms, "product_name": "SPIC CMS PRO 50 KG", "unit": "Bag", "qty": 160.0, "unit_price": 504.76, "amount": 80761.92, "batch_number": "CMSPRO50", "expiry_date": "2028-04-22"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_siri_id, "SIRIGUPPA AGRO AGENCIES", "SAA-271", "2026-04-22", "Main Warehouse", "Lorry", "Credit", "2026-04-22",
             "Scanned Siriguppa Invoice SAA-271", json.dumps(items2), 80761.92, 0.0, 2019.05, 2019.05, 84800.00, 0.0, 84800.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 3. SIRIGUPPA AGRO: SAA-54 (06-04-2026) ----------------
    p_spic_urea = await get_or_create_prod("SPIC UREA 45 KG", "Fertilizers", "Bag", 260.00, 275.00, "SPICUREA45", "2028-04-06", "SIRIGUPPA AGRO")
    await execute("UPDATE products SET current_stock = current_stock + 280 WHERE id = ?", (p_spic_urea,))

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SAA-54", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_spic_urea, "product_name": "SPIC UREA 45 KG", "unit": "Bag", "qty": 280.0, "unit_price": 247.62, "amount": 69333.26, "batch_number": "SPICUREA45", "expiry_date": "2028-04-06"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_siri_id, "SIRIGUPPA AGRO AGENCIES", "SAA-54", "2026-04-06", "Main Warehouse", "Lorry", "Credit", "2026-04-06",
             "Scanned Siriguppa Invoice SAA-54", json.dumps(items3), 69333.26, 0.0, 1733.33, 1733.33, 72800.00, 0.0, 72800.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 4. SLV AGRO TRADERS: SLV/26-27/532 (27-05-2026) ----------------
    p_koc1 = await get_or_create_prod("Kocide 1Kg", "Pesticides", "Packet", 1790.00, 1950.00, "25H3573VC4", "2027-05-04", "SRI LAKSHMI VENKATESWARA AGRO TRADERS")
    p_sef400 = await get_or_create_prod("Sefina 400Ml", "Pesticides", "Bottle", 2077.00, 2250.00, "DSE26001", "2026-11-04", "SRI LAKSHMI VENKATESWARA AGRO TRADERS")

    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_koc1,))
    await execute("UPDATE products SET current_stock = current_stock + 15 WHERE id = ?", (p_sef400,))

    inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SLV/26-27/532", owner_id))
    if not inv4:
        items4 = [
            {"product_id": p_koc1, "product_name": "Kocide 1Kg", "unit": "Packet", "qty": 20.0, "unit_price": 1516.95, "amount": 30339.00, "batch_number": "25H3573VC4", "expiry_date": "2027-05-04"},
            {"product_id": p_sef400, "product_name": "Sefina 400Ml", "unit": "Bottle", "qty": 15.0, "unit_price": 1760.17, "amount": 26402.55, "batch_number": "DSE26001", "expiry_date": "2026-11-04"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SLV/26-27/532", "2026-05-27", "Main Warehouse", "Direct", "Credit", "2026-05-27",
             "Scanned SLV Invoice SLV/26-27/532", json.dumps(items4), 56741.55, 0.0, 5106.74, 5106.74, 66955.00, 0.0, 66955.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 5. NEW INDIA CROP SCIENCE: NICS/25-26/608 (04-02-2026) ----------------
    p_min19 = await get_or_create_prod("MINERVA 19:19:19 25KG BAG", "Fertilizers", "Bag", 1701.00, 1850.00, "MIN191919", "2028-02-04", "NEW INDIA CROP SCIENCE")
    p_min20 = await get_or_create_prod("MINERVA 20:20:20 25KG BAG", "Fertilizers", "Bag", 1911.00, 2050.00, "MIN202020", "2028-02-04", "NEW INDIA CROP SCIENCE")
    p_min12 = await get_or_create_prod("MINERVA 12:61:00 25KG BAG", "Fertilizers", "Bag", 2310.00, 2500.00, "MIN126100", "2028-02-04", "NEW INDIA CROP SCIENCE")
    p_min13 = await get_or_create_prod("MINERVA 13:40:13 25KG BAG", "Fertilizers", "Bag", 2205.00, 2400.00, "MIN134013", "2028-02-04", "NEW INDIA CROP SCIENCE")
    p_min00 = await get_or_create_prod("MINERVA 00:52:34 25KG BAG", "Fertilizers", "Bag", 3003.00, 3200.00, "MIN005234", "2028-02-04", "NEW INDIA CROP SCIENCE")

    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_min19,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_min20,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_min12,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_min13,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_min00,))

    inv5 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("NICS/25-26/608", owner_id))
    if not inv5:
        items5 = [
            {"product_id": p_min19, "product_name": "MINERVA 19:19:19 25KG BAG", "unit": "Bag", "qty": 10.0, "unit_price": 1620.00, "amount": 16200.00, "batch_number": "MIN191919", "expiry_date": "2028-02-04"},
            {"product_id": p_min20, "product_name": "MINERVA 20:20:20 25KG BAG", "unit": "Bag", "qty": 10.0, "unit_price": 1820.00, "amount": 18200.00, "batch_number": "MIN202020", "expiry_date": "2028-02-04"},
            {"product_id": p_min12, "product_name": "MINERVA 12:61:00 25KG BAG", "unit": "Bag", "qty": 5.0, "unit_price": 2200.00, "amount": 11000.00, "batch_number": "MIN126100", "expiry_date": "2028-02-04"},
            {"product_id": p_min13, "product_name": "MINERVA 13:40:13 25KG BAG", "unit": "Bag", "qty": 5.0, "unit_price": 2100.00, "amount": 10500.00, "batch_number": "MIN134013", "expiry_date": "2028-02-04"},
            {"product_id": p_min00, "product_name": "MINERVA 00:52:34 25KG BAG", "unit": "Bag", "qty": 5.0, "unit_price": 2860.00, "amount": 14300.00, "batch_number": "MIN005234", "expiry_date": "2028-02-04"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nics_id, "NEW INDIA CROP SCIENCE", "NICS/25-26/608", "2026-02-04", "Main Warehouse", "Direct", "Credit", "2026-02-04",
             "Scanned NICS Invoice NICS/25-26/608", json.dumps(items5), 70200.00, 0.0, 1755.00, 1755.00, 73710.00, 0.0, 73710.00, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added 5 New Invoices (July 21) into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_5_new_july21_admin())
