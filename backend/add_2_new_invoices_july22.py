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

async def insert_2_new_invoices_july22_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding 2 New Invoices (July 22) for ADMIN user ({owner_id})...")

    # Supplier 1: SRI LAKSHMI VENKATESWARA AGRO TRADERS
    sup_slv = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("SRI LAKSHMI VENKATESWARA AGRO TRADERS", owner_id))
    if not sup_slv:
        sup_slv_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "9490583999", "slvatcv@gmail.com",
             "Sy No: 71/1-1, Beside KTR Function Hall, Gooty Road, Anantapuramu AP", "37ADHPV2108G1ZJ", -39600.00, owner_id, now_iso())
        )
    else:
        sup_slv_id = sup_slv["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount - 39600.00 WHERE id = ?", (sup_slv_id,))

    # Supplier 2: NEW INDIA CROP SCIENCE
    sup_nics = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("NEW INDIA CROP SCIENCE", owner_id))
    if not sup_nics:
        sup_nics_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_nics_id, "NEW INDIA CROP SCIENCE", "NEW INDIA CROP SCIENCE", "9703835362", "info@newindiacropscience.com",
             "D.No 17-01-272-03, Godown 4, Rapthadu, Anantapuramu - 515002 AP", "37AWWPB6419N1ZS", 51710.00, owner_id, now_iso())
        )
    else:
        sup_nics_id = sup_nics["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 51710.00 WHERE id = ?", (sup_nics_id,))

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
             f"89030407{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- 1. CREDIT NOTE: SR/26-27/57 (29-06-2026) ----------------
    p_sumi = await get_or_create_prod("Sumimax 10Ml*240", "Pesticides", "Nos", 93.22, 110.00, "BSMX602003", "2028-02-13", "SRI LAKSHMI VENKATESWARA AGRO TRADERS")
    # Return to supplier reduce stock
    await execute("UPDATE products SET current_stock = current_stock - 360 WHERE id = ?", (p_sumi,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SR/26-27/57", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_sumi, "product_name": "Sumimax 10Ml*240", "unit": "Nos", "qty": -360.0, "unit_price": 93.22, "amount": -33559.20, "batch_number": "BSMX602003", "expiry_date": "2028-02-13"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SR/26-27/57", "2026-06-29", "Main Warehouse", "Direct", "Credit Note", "2026-06-29",
             "Sales Return / Credit Note Ref SLV/26-27/1112", json.dumps(items1), -33559.20, 0.0, -3020.33, -3020.33, -39600.00, 0.0, -39600.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 2. NEW INDIA CROP SCIENCE: NICS/26-27/240 (26-06-2026) ----------------
    p_min19 = await get_or_create_prod("MINERVA 19:19:19 25KG BAG", "Fertilizers", "Bag", 1733.27, 1900.00, "NPK/19/6/26", "2028-06-26", "NEW INDIA CROP SCIENCE")
    p_min20 = await get_or_create_prod("MINERVA 20:20:20 25KG BAG", "Fertilizers", "Bag", 1904.69, 2100.00, "NPK/20/6/26", "2028-06-26", "NEW INDIA CROP SCIENCE")
    p_min12 = await get_or_create_prod("MINERVA 12:61:00 25KG BAG", "Fertilizers", "Bag", 2285.63, 2500.00, "MAP/12/6/26", "2028-06-26", "NEW INDIA CROP SCIENCE")

    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_min19,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_min20,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_min12,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("NICS/26-27/240", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_min19, "product_name": "MINERVA 19:19:19 25KG BAG", "unit": "Bag", "qty": 10.0, "unit_price": 1733.27, "amount": 17332.70, "batch_number": "NPK/19/6/26", "expiry_date": "2028-06-26"},
            {"product_id": p_min20, "product_name": "MINERVA 20:20:20 25KG BAG", "unit": "Bag", "qty": 10.0, "unit_price": 1904.69, "amount": 19046.90, "batch_number": "NPK/20/6/26", "expiry_date": "2028-06-26"},
            {"product_id": p_min12, "product_name": "MINERVA 12:61:00 25KG BAG", "unit": "Bag", "qty": 5.0, "unit_price": 2285.63, "amount": 11428.15, "batch_number": "MAP/12/6/26", "expiry_date": "2028-06-26"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nics_id, "NEW INDIA CROP SCIENCE", "NICS/26-27/240", "2026-06-26", "Main Warehouse", "Direct", "Credit", "2026-06-26",
             "Scanned NICS Invoice NICS/26-27/240", json.dumps(items2), 47807.75, 0.0, 1951.12, 1951.13, 51710.00, 0.0, 51710.00, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added 2 New Invoices (July 22) into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_2_new_invoices_july22_admin())
