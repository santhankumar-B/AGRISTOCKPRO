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

async def insert_srion_slvat_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding Srion Agri & SLV Agro Traders Invoices for ADMIN user ({owner_id})...")

    # Supplier 1: SRION AGRI SOLUTIONS PVT LTD
    sup_srion = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("SRION AGRI SOLUTIONS PVT LTD", owner_id))
    if not sup_srion:
        sup_srion_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_srion_id, "SRION AGRI SOLUTIONS PVT LTD", "SRION AGRI SOLUTIONS PVT LTD", "7416506401", "keerthi.kumar@srion.in",
             "D No:72-2-199, Etukuru Road, S K R Estate, R Agraharam, Guntur AP", "37ABFCS5526A1ZJ", 325596.00, owner_id, now_iso())
        )
    else:
        sup_srion_id = sup_srion["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 325596.00 WHERE id = ?", (sup_srion_id,))

    # Supplier 2: SRI LAKSHMI VENKATESWARA AGRO TRADERS
    sup_slv = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("SRI LAKSHMI VENKATESWARA AGRO TRADERS", owner_id))
    if not sup_slv:
        sup_slv_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "9490583999", "slvatcv@gmail.com",
             "Sy No: 71/1-1, Beside KTR Function Hall, Gooty Road, Anantapuramu AP", "37ADHPV2108G1ZJ", 174920.00, owner_id, now_iso())
        )
    else:
        sup_slv_id = sup_slv["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 174920.00 WHERE id = ?", (sup_slv_id,))

    # Helper to get/create product for Admin
    async def get_or_create_prod(name, cat, unit, price, sell_price, batch, exp, company="SRION AGRI SOLUTIONS"):
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
             f"89030400{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- SRION INVOICE 1: SIGNT0119/26-27 (25-05-2026) ----------------
    p_cal85_1 = await get_or_create_prod("CALION 85 - 1 LTR", "Pesticides", "Bottle", 1246.88, 1350.00, "CGA/C3508/25/013", "2028-07-31")
    p_eld1 = await get_or_create_prod("ELDMAX - 1 LTR", "Pesticides", "Bottle", 1613.00, 1750.00, "GB1025EM/06", "2027-10-06")
    p_glo1 = await get_or_create_prod("GLORY - 1 LTR", "Pesticides", "Bottle", 572.00, 630.00, "CGA/GR/04/26/001", "2027-03-31")
    p_sub1 = await get_or_create_prod("SUBTILE PRO - 1 LTR", "Pesticides", "Bottle", 1136.00, 1250.00, "BSSP05", "2029-04-30")
    p_sub500 = await get_or_create_prod("SUBTILE PRO - 500 ML", "Pesticides", "Bottle", 612.50, 680.00, "BSSP05", "2029-04-30")

    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_cal85_1,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_eld1,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_glo1,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_sub1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_sub500,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SIGNT0119/26-27", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_cal85_1, "product_name": "CALION 85 - 1 LTR", "unit": "Bottle", "qty": 20.0, "unit_price": 1187.50, "amount": 23750.00, "batch_number": "CGA/C3508/25/013", "expiry_date": "2028-07-31"},
            {"product_id": p_eld1, "product_name": "ELDMAX - 1 LTR", "unit": "Bottle", "qty": 10.0, "unit_price": 1536.19, "amount": 15361.90, "batch_number": "GB1025EM/06", "expiry_date": "2027-10-06"},
            {"product_id": p_glo1, "product_name": "GLORY - 1 LTR", "unit": "Bottle", "qty": 10.0, "unit_price": 544.76, "amount": 5447.60, "batch_number": "CGA/GR/04/26/001", "expiry_date": "2027-03-31"},
            {"product_id": p_sub1, "product_name": "SUBTILE PRO - 1 LTR", "unit": "Bottle", "qty": 10.0, "unit_price": 1081.90, "amount": 10819.00, "batch_number": "BSSP05", "expiry_date": "2029-04-30"},
            {"product_id": p_sub500, "product_name": "SUBTILE PRO - 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 583.33, "amount": 11666.70, "batch_number": "BSSP05", "expiry_date": "2029-04-30"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_srion_id, "SRION AGRI SOLUTIONS PVT LTD", "SIGNT0119/26-27", "2026-05-25", "Main Warehouse", "NAMRATHA", "Credit", "2026-05-25",
             "Scanned Srion Invoice SIGNT0119/26-27", json.dumps(items1), 67045.20, 0.0, 1676.14, 1676.14, 70397.00, 0.0, 70397.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- SRION INVOICE 2: SIGNT0135/26-27 (27-05-2026) ----------------
    p_sri700 = await get_or_create_prod("SRION-700 - 20 LTR", "Pesticides", "Can", 2879.94, 3100.00, "CGAPJST0526001", "2028-04-30")
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_sri700,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SIGNT0135/26-27", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_sri700, "product_name": "SRION-700 - 20 LTR", "unit": "Can", "qty": 20.0, "unit_price": 2742.80, "amount": 54856.00, "batch_number": "CGAPJST0526001", "expiry_date": "2028-04-30"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_srion_id, "SRION AGRI SOLUTIONS PVT LTD", "SIGNT0135/26-27", "2026-05-27", "Main Warehouse", "NAMRATHA", "Credit", "2026-05-27",
             "Scanned Srion Invoice SIGNT0135/26-27", json.dumps(items2), 54856.00, 0.0, 1371.40, 1371.40, 57599.00, 0.0, 57599.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- SRION INVOICE 3: SIGNT0063/26-27 (04-05-2026) ----------------
    p_zin1 = await get_or_create_prod("ZINON - 1 LTR", "Pesticides", "Bottle", 1596.57, 1720.00, "CGA/CVA025001/02", "2028-03-31")
    p_zin500 = await get_or_create_prod("ZINON - 500 ML", "Pesticides", "Bottle", 835.31, 910.00, "CGA/CVA025002", "2028-03-31")
    p_cal500 = await get_or_create_prod("CALION 85 - 500 ML", "Pesticides", "Bottle", 665.63, 730.00, "CGA/C35025003", "2028-07-31")
    p_eld500 = await get_or_create_prod("ELDMAX - 500 ML", "Pesticides", "Bottle", 851.00, 930.00, "GB0425EM/02", "2028-04-14")
    p_col1 = await get_or_create_prod("COLORS - 1 KG", "Pesticides", "Packet", 1399.00, 1500.00, "CGA/CS0705010", "2028-06-30")
    p_ene500 = await get_or_create_prod("ENERGY - 500 ML", "Pesticides", "Bottle", 659.00, 720.00, "638-17-0925", "2028-06-19")
    p_b500 = await get_or_create_prod("B-500 GMS", "Pesticides", "Packet", 828.50, 910.00, "CGA/PB0724007", "2027-06-30")
    p_push500 = await get_or_create_prod("PUSHPAL - 500 ML", "Pesticides", "Bottle", 808.00, 890.00, "CGA/PP1125002", "2026-10-31")
    p_boro1 = await get_or_create_prod("BORO20 - 1 KG", "Pesticides", "Packet", 427.35, 470.00, "CGA/B20/02/25/07", "2027-01-31")

    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_zin1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_zin500,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_cal500,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_eld500,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_sub500,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_col1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_ene500,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_b500,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_glo1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_push500,))
    await execute("UPDATE products SET current_stock = current_stock + 100 WHERE id = ?", (p_boro1,))

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SIGNT0063/26-27", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_zin1, "product_name": "ZINON - 1 LTR", "unit": "Bottle", "qty": 10.0, "unit_price": 1520.54, "amount": 15205.40, "batch_number": "CGA/CVA025001/02", "expiry_date": "2028-03-31"},
            {"product_id": p_zin500, "product_name": "ZINON - 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 795.54, "amount": 15910.70, "batch_number": "CGA/CVA025002", "expiry_date": "2028-03-31"},
            {"product_id": p_cal500, "product_name": "CALION 85 - 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 633.93, "amount": 12678.60, "batch_number": "CGA/C35025003", "expiry_date": "2028-07-31"},
            {"product_id": p_eld500, "product_name": "ELDMAX - 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 810.48, "amount": 16209.50, "batch_number": "GB0425EM/02", "expiry_date": "2028-04-14"},
            {"product_id": p_sub500, "product_name": "SUBTILE PRO - 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 583.33, "amount": 11666.70, "batch_number": "BSSP10", "expiry_date": "2027-09-30"},
            {"product_id": p_col1, "product_name": "COLORS - 1 KG", "unit": "Packet", "qty": 20.0, "unit_price": 1332.38, "amount": 26647.60, "batch_number": "CGA/CS0705010", "expiry_date": "2028-06-30"},
            {"product_id": p_ene500, "product_name": "ENERGY - 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 627.62, "amount": 12552.40, "batch_number": "638-17-0925", "expiry_date": "2028-06-19"},
            {"product_id": p_b500, "product_name": "B-500 GMS", "unit": "Packet", "qty": 20.0, "unit_price": 789.05, "amount": 15781.00, "batch_number": "CGA/PB0724007", "expiry_date": "2027-06-30"},
            {"product_id": p_glo1, "product_name": "GLORY - 1 LTR", "unit": "Bottle", "qty": 10.0, "unit_price": 544.76, "amount": 5447.60, "batch_number": "CGA/GR/11/25/008", "expiry_date": "2026-10-31"},
            {"product_id": p_push500, "product_name": "PUSHPAL - 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 769.53, "amount": 15390.60, "batch_number": "CGA/PP1125002", "expiry_date": "2026-10-31"},
            {"product_id": p_boro1, "product_name": "BORO20 - 1 KG", "unit": "Packet", "qty": 100.0, "unit_price": 407.00, "amount": 40700.00, "batch_number": "CGA/B20/02/25/07", "expiry_date": "2027-01-31"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_srion_id, "SRION AGRI SOLUTIONS PVT LTD", "SIGNT0063/26-27", "2026-05-04", "Main Warehouse", "NAMRATHA", "Credit", "2026-05-04",
             "Scanned Srion Invoice SIGNT0063/26-27", json.dumps(items3), 188190.10, 0.0, 4704.78, 4704.78, 197600.00, 0.0, 197600.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- SLV INVOICE 1: SLV/26-27/06 (02-04-2026) ----------------
    p_mag500 = await get_or_create_prod("Magister 500Ml", "Pesticides", "Bottle", 1085.00, 1200.00, "2516233607", "2027-09-17", "SRI LAKSHMI VENKATESWARA AGRO TRADERS")
    p_gal1 = await get_or_create_prod("Galwan 1Lt", "Pesticides", "Bottle", 1050.00, 1160.00, "S/KRE-50", "2027-08-20", "SRI LAKSHMI VENKATESWARA AGRO TRADERS")
    p_gal500 = await get_or_create_prod("Galwan 500Ml", "Pesticides", "Bottle", 543.00, 600.00, "S/KRE-49", "2027-08-05", "SRI LAKSHMI VENKATESWARA AGRO TRADERS")
    p_han200 = await get_or_create_prod("Hanabi 200Gms", "Pesticides", "Packet", 882.00, 980.00, "GJ0725004", "2027-07-28", "SRI LAKSHMI VENKATESWARA AGRO TRADERS")

    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_mag500,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_gal1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_gal500,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_han200,))

    inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SLV/26-27/06", owner_id))
    if not inv4:
        items4 = [
            {"product_id": p_mag500, "product_name": "Magister 500Ml", "unit": "Bottle", "qty": 20.0, "unit_price": 919.49, "amount": 18389.80, "batch_number": "2516233607", "expiry_date": "2027-09-17"},
            {"product_id": p_gal1, "product_name": "Galwan 1Lt", "unit": "Bottle", "qty": 10.0, "unit_price": 889.83, "amount": 8898.30, "batch_number": "S/KRE-50", "expiry_date": "2027-08-20"},
            {"product_id": p_gal500, "product_name": "Galwan 500Ml", "unit": "Bottle", "qty": 20.0, "unit_price": 460.17, "amount": 9203.40, "batch_number": "S/KRE-49", "expiry_date": "2027-08-05"},
            {"product_id": p_han200, "product_name": "Hanabi 200Gms", "unit": "Packet", "qty": 10.0, "unit_price": 747.46, "amount": 7474.60, "batch_number": "GJ0725004", "expiry_date": "2027-07-28"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SLV/26-27/06", "2026-04-02", "Main Warehouse", "Direct", "Credit", "2026-04-02",
             "Scanned SLV Invoice SLV/26-27/06", json.dumps(items4), 43966.10, 0.0, 3956.95, 3956.95, 51880.00, 0.0, 51880.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- SLV INVOICE 2: SLV/26-27/80 (11-04-2026) ----------------
    p_koc1 = await get_or_create_prod("Kocide 1Kg", "Pesticides", "Packet", 1790.00, 1950.00, "2583573VC4", "2027-02-25", "SRI LAKSHMI VENKATESWARA AGRO TRADERS")
    p_koc500 = await get_or_create_prod("Kocide 500Gms", "Pesticides", "Packet", 917.00, 1000.00, "25H3569K05", "2027-02-25", "SRI LAKSHMI VENKATESWARA AGRO TRADERS")

    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_koc1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_koc500,))
    await execute("UPDATE products SET current_stock = current_stock + 80 WHERE id = ?", (p_mag500,))

    inv5 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SLV/26-27/80", owner_id))
    if not inv5:
        items5 = [
            {"product_id": p_koc1, "product_name": "Kocide 1Kg", "unit": "Packet", "qty": 10.0, "unit_price": 1516.95, "amount": 15169.50, "batch_number": "2583573VC4", "expiry_date": "2027-02-25"},
            {"product_id": p_koc500, "product_name": "Kocide 500Gms", "unit": "Packet", "qty": 20.0, "unit_price": 777.12, "amount": 15542.40, "batch_number": "25H3569K05", "expiry_date": "2027-02-25"},
            {"product_id": p_mag500, "product_name": "Magister 500Ml", "unit": "Bottle", "qty": 80.0, "unit_price": 919.49, "amount": 73559.20, "batch_number": "25H6233005", "expiry_date": "2027-09-17"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SLV/26-27/80", "2026-04-11", "Main Warehouse", "Direct", "Credit", "2026-04-11",
             "Scanned SLV Invoice SLV/26-27/80", json.dumps(items5), 104271.10, 0.0, 9384.41, 9384.41, 123040.00, 0.0, 123040.00, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added Srion Agri & SLV Agro Traders invoices into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_srion_slvat_admin())
