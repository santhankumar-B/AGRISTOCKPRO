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

async def insert_5_new_invoices():
    init_db()
    users = await fetch_all("SELECT * FROM users")
    if not users:
        print("No users found.")
        return

    for u in users:
        owner_id = u["id"]
        username = u["username"]
        print(f"Adding 5 Scanned Invoices for user: {username}...")

        # Supplier: T. STANES AND COMPANY LIMITED
        sup = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("T. STANES AND COMPANY LIMITED", owner_id))
        if not sup:
            sup_id = uid()
            await execute(
                """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sup_id, "T. STANES AND COMPANY LIMITED", "T. STANES AND COMPANY LIMITED", "6374712405", "info@tstanes.com",
                 "D.No 76/97/3-4-A Beside Hanuman Weigh Bridge, Bellary Road, Kurnool - 518003", "37AAACT7126P1ZU", 310961.00, owner_id, now_iso())
            )
        else:
            sup_id = sup["id"]
            await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 241961.00 WHERE id = ?", (sup_id,))

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

        # ---------------- INVOICE 1: 303101220001 (03-04-2026) ----------------
        pid_addon = await get_or_create_prod("ADDON (NPK-19-19-19) 25KG", "Fertilizers", "Bag", 3528.00, 3600.00, "1919190925", "2028-09-07")
        pid_infuse = await get_or_create_prod("INFUSE (POTASSIUM SULPHATE) 25KG", "Fertilizers", "Bag", 2746.00, 2850.00, "TS/SOP0725", "2028-08-08")
        pid_takeon = await get_or_create_prod("TAKEON (MONO POTASSIUM PHOSPHATE) 25KG", "Fertilizers", "Bag", 4908.00, 5050.00, "S829684/25", "2028-08-08")

        await execute("UPDATE products SET current_stock = current_stock + 9 WHERE id = ?", (pid_addon,))
        await execute("UPDATE products SET current_stock = current_stock + 2 WHERE id = ?", (pid_infuse,))
        await execute("UPDATE products SET current_stock = current_stock + 2 WHERE id = ?", (pid_takeon,))

        inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303101220001", owner_id))
        if not inv1:
            items1 = [
                {"product_id": pid_addon, "product_name": "ADDON (NPK-19-19-19) 25KG", "unit": "Bag", "qty": 9.0, "unit_price": 3528.00, "amount": 31752.00, "batch_number": "1919190925", "expiry_date": "2028-09-07"},
                {"product_id": pid_infuse, "product_name": "INFUSE (POTASSIUM SULPHATE) 25KG", "unit": "Bag", "qty": 2.0, "unit_price": 2746.00, "amount": 5492.00, "batch_number": "TS/SOP0725", "expiry_date": "2028-08-08"},
                {"product_id": pid_takeon, "product_name": "TAKEON (MONO POTASSIUM PHOSPHATE) 25KG", "unit": "Bag", "qty": 2.0, "unit_price": 4908.00, "amount": 9816.00, "batch_number": "S829684/25", "expiry_date": "2028-08-08"},
            ]
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303101220001", "2026-04-03", "Main Warehouse", "O/NANDEESWAR", "Credit", "2026-04-03",
                 "Scanned Tax Invoice 303101220001", json.dumps(items1), 52000.00, 4940.00, 1176.50, 1176.50, 49413.00, 0.0, 49413.00, "Credit", "posted", owner_id, now_iso())
            )

        # ---------------- INVOICE 2: 303101220016 (15-06-2026) ----------------
        pid_hugo = await get_or_create_prod("HUGO (POTASSIUM NITRATE) 25KG", "Fertilizers", "Bag", 3275.00, 3400.00, "TS/PN/0426", "2030-04-29")
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (pid_hugo,))

        inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303101220016", owner_id))
        if not inv2:
            items2 = [
                {"product_id": pid_hugo, "product_name": "HUGO (POTASSIUM NITRATE) 25KG", "unit": "Bag", "qty": 20.0, "unit_price": 3275.00, "amount": 65500.00, "batch_number": "TS/PN/0426", "expiry_date": "2030-04-29"}
            ]
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303101220016", "2026-06-15", "Main Warehouse", "O/NANDESWARA", "Credit", "2026-06-15",
                 "Scanned Tax Invoice 303101220016", json.dumps(items2), 85000.00, 19500.00, 1637.50, 1637.50, 68775.00, 0.0, 68775.00, "Credit", "posted", owner_id, now_iso())
            )

        # ---------------- INVOICE 3: 303102220039 (30-05-2026) ----------------
        pid_microfood = await get_or_create_prod("STANES MICROFOOD LIQUID MICRONUTRIENTS 5 LT", "Bio-Fertilizers", "Can", 1669.00, 1800.00, "114", "2027-07-03")
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (pid_microfood,))

        inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303102220039", owner_id))
        if not inv3:
            items3 = [
                {"product_id": pid_microfood, "product_name": "STANES MICROFOOD LIQUID MICRONUTRIENTS 5 LT", "unit": "Can", "qty": 10.0, "unit_price": 1669.00, "amount": 16690.00, "batch_number": "114", "expiry_date": "2027-07-03"}
            ]
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303102220039", "2026-05-30", "Main Warehouse", "O/NANDESWARA", "Credit", "2026-05-30",
                 "Scanned Tax Invoice 303102220039", json.dumps(items3), 50000.00, 23250.00, 417.25, 417.25, 17524.00, 0.0, 17524.00, "Credit", "posted", owner_id, now_iso())
            )

        # ---------------- INVOICE 4: 303101220009 (30-05-2026) ----------------
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (pid_takeon,))
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (pid_hugo,))

        inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303101220009", owner_id))
        if not inv4:
            items4 = [
                {"product_id": pid_takeon, "product_name": "TAKEON (MONO POTASSIUM PHOSPHATE) 25KG", "unit": "Bag", "qty": 10.0, "unit_price": 3400.00, "amount": 34000.00, "batch_number": "TS/MKP0426", "expiry_date": "2030-04-29"},
                {"product_id": pid_hugo, "product_name": "HUGO (POTASSIUM NITRATE) 25KG", "unit": "Bag", "qty": 20.0, "unit_price": 2506.50, "amount": 50130.00, "batch_number": "TS/PN/0426", "expiry_date": "2030-04-29"},
            ]
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303101220009", "2026-05-30", "Main Warehouse", "O/NANDESWARA", "Credit", "2026-05-30",
                 "Scanned Tax Invoice 303101220009", json.dumps(items4), 106500.00, 22370.00, 2103.25, 2103.25, 88336.00, 0.0, 88336.00, "Credit", "posted", owner_id, now_iso())
            )

        # ---------------- INVOICE 5: 303103220144 (25-06-2026) ----------------
        pid_wektocon = await get_or_create_prod("WEKTOCON 1LT", "Bio-Pesticides", "Bottle", 1535.00, 1680.00, "WK022635", "2028-01-21")
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (pid_wektocon,))

        inv5 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("303103220144", owner_id))
        if not inv5:
            items5 = [
                {"product_id": pid_wektocon, "product_name": "WEKTOCON 1LT", "unit": "Bottle", "qty": 10.0, "unit_price": 1535.00, "amount": 15350.00, "batch_number": "WK022635", "expiry_date": "2028-01-21"}
            ]
            await execute(
                """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid(), sup_id, "T. STANES AND COMPANY LIMITED", "303103220144", "2026-06-25", "Main Warehouse", "O/NANDESWARA", "Credit", "2026-06-25",
                 "Scanned Tax Invoice 303103220144", json.dumps(items5), 20000.00, 4650.00, 1381.50, 1381.50, 18113.00, 0.0, 18113.00, "Credit", "posted", owner_id, now_iso())
            )

    print("5 new scanned T. Stanes invoices successfully inserted into database!")

if __name__ == "__main__":
    asyncio.run(insert_5_new_invoices())
