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

async def add_stanes_invoice_2():
    init_db()
    
    users = await fetch_all("SELECT * FROM users")
    if not users:
        print("No users found.")
        return

    for user in users:
        owner_id = user["id"]
        username = user["username"]
        print(f"Adding 2nd invoice data for user: {username} ({owner_id})...")

        sup_name = "T. STANES AND COMPANY LIMITED"
        existing_s = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", (sup_name, owner_id))
        
        if existing_s:
            sid = existing_s["id"]
            await execute(
                "UPDATE suppliers SET outstanding_amount = outstanding_amount + 19667.0 WHERE id = ? AND owner_id = ?",
                (sid, owner_id)
            )
        else:
            sid = uid()
            await execute(
                """INSERT INTO suppliers (
                    id, owner_id, name, company, phone, email, address, gst, bank_name,
                    bank_account, ifsc, opening_balance, outstanding_amount, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sid, owner_id, sup_name, sup_name, "6374712405", "info@tstanes.com",
                    "D.No 76/97/3-4-A Beside Hanuman Weigh Bridge, Bellary Road, Kurnool - 518003",
                    "37AAACT7126P1ZU", "HDFC BANK LTD", "TS186128303B0063", "HDFC0000031",
                    0.0, 19667.0, "active", now_iso()
                )
            )

        # 1. Product 1: ADDON (NPK-19-19-19) 25KG
        p1_name = "ADDON (NPK-19-19-19) 25KG"
        existing_p1 = await fetch_one("SELECT * FROM products WHERE name = ? AND owner_id = ?", (p1_name, owner_id))
        if existing_p1:
            p1_id = existing_p1["id"]
            await execute(
                """UPDATE products SET 
                    current_stock = current_stock + 125.0,
                    purchase_price = 121.80,
                    selling_price = 3105.00,
                    batch_number = '1919190426',
                    expiry_date = '2030-04-29'
                WHERE id = ? AND owner_id = ?""",
                (p1_id, owner_id)
            )
        else:
            p1_id = uid()
            await execute(
                """INSERT INTO products (
                    id, owner_id, name, category, company, brand, barcode, batch_number,
                    manufacture_date, expiry_date, unit, purchase_price, selling_price,
                    current_stock, minimum_stock, rack_number, image_url, description, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    p1_id, owner_id, p1_name, "Fertilizers", "T. STANES AND COMPANY LIMITED",
                    "T. STANES", "31052000", "1919190426", "2026-04-01", "2030-04-29",
                    "KG", 121.80, 3105.00, 125.0, 25.0, "A-03", "", "19:19:19 NPK Water Soluble Fertilizer", now_iso()
                )
            )

        # 2. Product 2: HUGO (POTASSIUM NITRATE) 1KG
        p2_name = "HUGO (POTASSIUM NITRATE) 1KG"
        existing_p2 = await fetch_one("SELECT * FROM products WHERE name = ? AND owner_id = ?", (p2_name, owner_id))
        if existing_p2:
            p2_id = existing_p2["id"]
            await execute(
                """UPDATE products SET 
                    current_stock = current_stock + 25.0,
                    purchase_price = 142.60,
                    selling_price = 335.00,
                    batch_number = 'TS/PN/0426',
                    expiry_date = '2030-04-29'
                WHERE id = ? AND owner_id = ?""",
                (p2_id, owner_id)
            )
        else:
            p2_id = uid()
            await execute(
                """INSERT INTO products (
                    id, owner_id, name, category, company, brand, barcode, batch_number,
                    manufacture_date, expiry_date, unit, purchase_price, selling_price,
                    current_stock, minimum_stock, rack_number, image_url, description, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    p2_id, owner_id, p2_name, "Fertilizers", "T. STANES AND COMPANY LIMITED",
                    "T. STANES", "31059010", "TS/PN/0426", "2026-04-01", "2030-04-29",
                    "KG", 142.60, 335.00, 25.0, 5.0, "A-04", "", "13:0:45 Potassium Nitrate Water Soluble Fertilizer", now_iso()
                )
            )

        # 3. Purchase Invoice
        inv_no = "303101220021"
        existing_pur = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", (inv_no, owner_id))
        
        if not existing_pur:
            items_data = [
                {
                    "product_id": p1_id,
                    "product_name": p1_name,
                    "unit": "KG",
                    "qty": 125.0,
                    "unit_price": 121.80,
                    "amount": 15225.00,
                    "batch_number": "1919190426",
                    "expiry_date": "2030-04-29"
                },
                {
                    "product_id": p2_id,
                    "product_name": p2_name,
                    "unit": "KG",
                    "qty": 25.0,
                    "unit_price": 142.60,
                    "amount": 3565.00,
                    "batch_number": "TS/PN/0426",
                    "expiry_date": "2030-04-29"
                }
            ]
            await execute(
                """INSERT INTO purchases (
                    id, owner_id, supplier_id, supplier_name, invoice_number, invoice_date,
                    warehouse, reference_number, transporter, payment_terms, delivery_date,
                    notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount,
                    due_amount, payment_method, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    uid(), owner_id, sid, sup_name, inv_no, "2026-06-29",
                    "Kurnool Godown", "IRN-39509a04ca3", "O/NANDESWARA", "Credit", "2026-06-29",
                    "Scanned Tax Invoice 303101220021", json.dumps(items_data),
                    24500.00, 5770.00, 468.26, 468.26, 19667.00, 0.0, 19667.00,
                    "Credit", "posted", now_iso()
                )
            )
            print(f"Purchase invoice {inv_no} inserted successfully!")

if __name__ == "__main__":
    asyncio.run(add_stanes_invoice_2())
