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

async def insert_4_more_invoices():
    init_db()
    users = await fetch_all("SELECT * FROM users")
    if not users:
        print("No users found.")
        return

    for u in users:
        owner_id = u["id"]
        username = u["username"]
        print(f"Adding 4 Scanned Invoices for user: {username}...")

        # Supplier: T. STANES AND COMPANY LIMITED
        sup = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("T. STANES AND COMPANY LIMITED", owner_id))
        if not sup:
            sup_id = uid()
            await execute(
                """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sup_id, "T. STANES AND COMPANY LIMITED", "T. STANES AND COMPANY LIMITED", "6374712405", "info@tstanes.com",
                 "D.No 76/97/3-4-A Beside Hanuman Weigh Bridge, Bellary Road, Kurnool - 518003", "37AAACT7126P1ZU", 610523.28, owner_id, now_iso())
            )
        else:
            sup_id = sup["id"]
            await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 299562.28 WHERE id = ?", (sup_id,))

        # Helper to get/create product
        async def get_or_create_prod(name, cat, unit, price, sell_price, batch, exp):
            p = await fetch_one("SELECT * FROM products WHERE name = ? AND owner_id = ?", (name, owner_id))
            if p:
                return p["id"]
            pid = uid()
            await execute(
                """INSERT INTO products (id, name, category, company, brand, barcode, current_stock, minimum_stock, unit, purchase_price, selling_price, batch_number, expiry_date, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (pid, name, cat, "T. STANES AND COMPANY LIMITED", "T. STANES",
                 f"89030310{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
            )
            return pid

        # ---------------- INVOICE 1: 303102220014 (09-05-2026) ----------------
        p1 = await get_or_create_prod("STANES MICROFOOD LIQUID MICRONUTRIENTS 1 LT", "Bio-Fertilizers", "Bottle", 390.00, 440.00, "102", "2027-06-21")
        p2 = await get_or_create_prod("STANES MICROFOOD SPECIAL FOLIAR SPRAY ALL CROP FOLIAR 500 GM", "Bio-Fertilizers", "Packet", 120.75, 145.00, "MFF1025234", "2028-10-27")
        p3 = await get_or_create_prod("STANES MICROFOOD SPECIAL FOLIAR SPRAY ALL CROP FOLIAR 1 KG", "Bio-Fertilizers", "Packet", 235.50, 260.00, "MFF0226308", "2029-02-27")
        p4 = await get_or_create_prod("STANES MICROFOOD LIQUID MICRONUTRIENTS 500 ML", "Bio-Fertilizers", "Bottle", 207.50, 240.00, "LMF1225195", "2027-11-29")

        await execute("UPDATE products SET current_stock = current_stock + 50 WHERE id = ?", (p1,))
        await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p2,))
        await execute("UPDATE products SET current_stock = current_stock + 100 WHERE id = ?", (p3,))
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p4,))

        inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303102220014", owner_id))
        if not inv1:
            items1 = [
                {"product_id": p1, "product_name": "STANES MICROFOOD LIQUID MICRONUTRIENTS 1 LT", "unit": "Bottle", "qty": 50.0, "unit_price": 390.00, "amount": 19500.00, "batch_number": "102", "expiry_date": "2027-06-21"},
                {"product_id": p2, "product_name": "STANES MICROFOOD SPECIAL FOLIAR SPRAY ALL CROP FOLIAR 500 GM", "unit": "Packet", "qty": 40.0, "unit_price": 120.75, "amount": 4830.00, "batch_number": "MFF1025234", "expiry_date": "2028-10-27"},
                {"product_id": p3, "product_name": "STANES MICROFOOD SPECIAL FOLIAR SPRAY ALL CROP FOLIAR 1 KG", "unit": "Packet", "qty": 100.0, "unit_price": 235.50, "amount": 23550.00, "batch_number": "MFF0226308", "expiry_date": "2029-02-27"},
                {"product_id": p4, "product_name": "STANES MICROFOOD LIQUID MICRONUTRIENTS 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 207.50, "amount": 4150.00, "batch_number": "LMF1225195", "expiry_date": "2027-11-29"},
            ]
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303102220014", "2026-05-09", "Main Warehouse", "O/NANDEESWAR", "Credit", "2026-05-09",
                 "Scanned Tax Invoice 303102220014", json.dumps(items1), 58030.00, 6000.00, 1300.75, 1300.75, 54632.00, 0.0, 54632.00, "Credit", "posted", owner_id, now_iso())
            )

        # ---------------- INVOICE 2: 303103220037 (09-05-2026) ----------------
        p5 = await get_or_create_prod("LIQUID BIONEMATON (Paecilomyces Lilacinus) 1 LT", "Bio-Pesticides", "Bottle", 360.00, 410.00, "BN392", "2027-01-22")
        p6 = await get_or_create_prod("STANOWET 250ML", "Bio-Pesticides", "Bottle", 165.00, 190.00, "ST072515", "2027-07-14")
        p7 = await get_or_create_prod("WEKTOCON 1LT", "Bio-Pesticides", "Bottle", 1535.00, 1680.00, "WK102522", "2027-09-16")
        p8 = await get_or_create_prod("NIMBECIDINE 10000 PPM (TS) 250ML", "Bio-Pesticides", "Bottle", 592.50, 650.00, "S12510005", "2027-09-29")
        p9 = await get_or_create_prod("NIMBECIDINE 300 PPM (TS) 1LT", "Bio-Pesticides", "Bottle", 540.00, 600.00, "S0-032602018", "2028-02-16")
        p10 = await get_or_create_prod("NIMBECIDINE 300 PPM (TS) 500ML", "Bio-Pesticides", "Bottle", 275.00, 310.00, "S0-032602018", "2028-02-16")
        p11 = await get_or_create_prod("WEKTOCON 500ML", "Bio-Pesticides", "Bottle", 1005.00, 1120.00, "WK122532", "2027-11-19")

        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p5,))
        await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p6,))
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p7,))
        await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p8,))
        await execute("UPDATE products SET current_stock = current_stock + 50 WHERE id = ?", (p9,))
        await execute("UPDATE products SET current_stock = current_stock + 16 WHERE id = ?", (p10,))
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p11,))

        inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303103220037", owner_id))
        if not inv2:
            items2 = [
                {"product_id": p5, "product_name": "LIQUID BIONEMATON (Paecilomyces Lilacinus) 1 LT", "unit": "Bottle", "qty": 20.0, "unit_price": 360.00, "amount": 7200.00, "batch_number": "BN392", "expiry_date": "2027-01-22"},
                {"product_id": p6, "product_name": "STANOWET 250ML", "unit": "Bottle", "qty": 40.0, "unit_price": 165.00, "amount": 6600.00, "batch_number": "ST072515", "expiry_date": "2027-07-14"},
                {"product_id": p7, "product_name": "WEKTOCON 1LT", "unit": "Bottle", "qty": 10.0, "unit_price": 1535.00, "amount": 15350.00, "batch_number": "WK102522", "expiry_date": "2027-09-16"},
                {"product_id": p8, "product_name": "NIMBECIDINE 10000 PPM (TS) 250ML", "unit": "Bottle", "qty": 40.0, "unit_price": 592.50, "amount": 23700.00, "batch_number": "S12510005", "expiry_date": "2027-09-29"},
                {"product_id": p9, "product_name": "NIMBECIDINE 300 PPM (TS) 1LT", "unit": "Bottle", "qty": 50.0, "unit_price": 540.00, "amount": 27000.00, "batch_number": "S0-032602018", "expiry_date": "2028-02-16"},
                {"product_id": p10, "product_name": "NIMBECIDINE 300 PPM (TS) 500ML", "unit": "Bottle", "qty": 16.0, "unit_price": 275.00, "amount": 4400.00, "batch_number": "S0-032602018", "expiry_date": "2028-02-16"},
                {"product_id": p11, "product_name": "WEKTOCON 500ML", "unit": "Bottle", "qty": 20.0, "unit_price": 1005.00, "amount": 20100.00, "batch_number": "WK122532", "expiry_date": "2027-11-19"},
            ]
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303103220037", "2026-05-09", "Main Warehouse", "O/NANDESWARA", "Credit", "2026-05-09",
                 "Scanned Tax Invoice 303103220037", json.dumps(items2), 115600.00, 26182.00, 4596.64, 4596.64, 98611.28, 0.0, 98611.28, "Credit", "posted", owner_id, now_iso())
            )

        # ---------------- INVOICE 3: 303103220070 (04-06-2026) ----------------
        p12 = await get_or_create_prod("STANES GREEN MIRACLE (STRESS ALLEVIATOR) 1 LT", "Bio-Pesticides", "Bottle", 545.00, 600.00, "GM0526112", "2028-04-28")
        p13 = await get_or_create_prod("STANES GREEN MIRACLE (STRESS ALLEVIATOR) 500 ML", "Bio-Pesticides", "Bottle", 277.50, 310.00, "GM0526104", "2028-04-27")
        p14 = await get_or_create_prod("STANES GREEN MIRACLE (STRESS ALLEVIATOR) 5 LT", "Bio-Pesticides", "Can", 2675.00, 2900.00, "GM0526106", "2028-04-28")

        await execute("UPDATE products SET current_stock = current_stock + 50 WHERE id = ?", (p12,))
        await execute("UPDATE products SET current_stock = current_stock + 80 WHERE id = ?", (p13,))
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p14,))

        inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303103220070", owner_id))
        if not inv3:
            items3 = [
                {"product_id": p12, "product_name": "STANES GREEN MIRACLE (STRESS ALLEVIATOR) 1 LT", "unit": "Bottle", "qty": 50.0, "unit_price": 545.00, "amount": 27250.00, "batch_number": "GM0526112", "expiry_date": "2028-04-28"},
                {"product_id": p13, "product_name": "STANES GREEN MIRACLE (STRESS ALLEVIATOR) 500 ML", "unit": "Bottle", "qty": 80.0, "unit_price": 277.50, "amount": 22200.00, "batch_number": "GM0526104", "expiry_date": "2028-04-27"},
                {"product_id": p14, "product_name": "STANES GREEN MIRACLE (STRESS ALLEVIATOR) 5 LT", "unit": "Can", "qty": 20.0, "unit_price": 2675.00, "amount": 53500.00, "batch_number": "GM0526106", "expiry_date": "2028-04-28"},
            ]
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303103220070", "2026-06-04", "Main Warehouse", "O/NANDESWAR", "Credit", "2026-06-04",
                 "Scanned Tax Invoice 303103220070", json.dumps(items3), 102950.00, 23336.00, 7165.26, 7165.26, 93945.00, 0.0, 93945.00, "Credit", "posted", owner_id, now_iso())
            )

        # ---------------- INVOICE 4: 303102220050 (09-06-2026) ----------------
        p15 = await get_or_create_prod("STANES MICROFOOD LIQUID MICRONUTRIENTS 20 LT", "Bio-Fertilizers", "Can", 9200.00, 9800.00, "LMF052646V21", "2028-04-27")
        await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p15,))
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p1,))

        inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303102220050", owner_id))
        if not inv4:
            items4 = [
                {"product_id": p15, "product_name": "STANES MICROFOOD LIQUID MICRONUTRIENTS 20 LT", "unit": "Can", "qty": 5.0, "unit_price": 9200.00, "amount": 46000.00, "batch_number": "LMF052646V21", "expiry_date": "2028-04-27"},
                {"product_id": p1, "product_name": "STANES MICROFOOD LIQUID MICRONUTRIENTS 5 LT", "unit": "Can", "qty": 10.0, "unit_price": 2325.00, "amount": 23250.00, "batch_number": "114", "expiry_date": "2027-07-03"},
            ]
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303102220050", "2026-06-09", "Main Warehouse", "O/NANDESWARA", "Credit", "2026-06-09",
                 "Scanned Tax Invoice 303102220050", json.dumps(items4), 69250.00, 19370.00, 1247.00, 1247.00, 52374.00, 0.0, 52374.00, "Credit", "posted", owner_id, now_iso())
            )

    print("4 new scanned T. Stanes invoices successfully inserted into database!")

if __name__ == "__main__":
    asyncio.run(insert_4_more_invoices())
