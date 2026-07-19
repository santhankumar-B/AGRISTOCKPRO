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

async def add_stanes_invoice():
    init_db()
    
    users = await fetch_all("SELECT * FROM users")
    if not users:
        print("No users found.")
        return

    for user in users:
        owner_id = user["id"]
        username = user["username"]
        print(f"Adding invoice data for user: {username} ({owner_id})...")

        # 1. Product
        prod_name = "LIQUID BIONEMATON (Paecilomyces Lilacinus) 1 LT"
        existing_p = await fetch_one("SELECT * FROM products WHERE name = ? AND owner_id = ?", (prod_name, owner_id))
        
        if existing_p:
            pid = existing_p["id"]
            # Update stock and details
            await execute(
                """UPDATE products SET 
                    current_stock = current_stock + 40.0,
                    purchase_price = 272.20,
                    selling_price = 846.00,
                    batch_number = 'BN062604',
                    expiry_date = '2027-06-24',
                    company = 'T. STANES AND COMPANY LIMITED',
                    brand = 'T. STANES',
                    unit = 'LTR'
                WHERE id = ? AND owner_id = ?""",
                (pid, owner_id)
            )
        else:
            pid = uid()
            await execute(
                """INSERT INTO products (
                    id, owner_id, name, category, company, brand, barcode, batch_number,
                    manufacture_date, expiry_date, unit, purchase_price, selling_price,
                    current_stock, minimum_stock, rack_number, image_url, description, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pid, owner_id, prod_name, "Bio-Pesticides", "T. STANES AND COMPANY LIMITED",
                    "T. STANES", "30029030", "BN062604", "2026-06-01", "2027-06-24",
                    "LTR", 272.20, 846.00, 40.0, 10.0, "B-01", "", "Bio-Nematicide for soil treatment", now_iso()
                )
            )

        # 2. Supplier
        sup_name = "T. STANES AND COMPANY LIMITED"
        existing_s = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", (sup_name, owner_id))
        
        if existing_s:
            sid = existing_s["id"]
            await execute(
                "UPDATE suppliers SET outstanding_amount = outstanding_amount + 11432.0 WHERE id = ? AND owner_id = ?",
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
                    0.0, 11432.0, "active", now_iso()
                )
            )

        # 3. Purchase Invoice
        inv_no = "303103220172"
        existing_pur = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", (inv_no, owner_id))
        
        if not existing_pur:
            items_data = [
                {
                    "product_id": pid,
                    "product_name": prod_name,
                    "unit": "LTR",
                    "qty": 40.0,
                    "unit_price": 272.20,
                    "amount": 10888.00,
                    "batch_number": "BN062604",
                    "expiry_date": "2027-06-24"
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
                    uid(), owner_id, sid, sup_name, inv_no, "2026-07-06",
                    "Kurnool Godown", "IRN-ac191e1639c", "O/NANDESWARA", "Credit", "2026-07-06",
                    "Scanned Tax Invoice 303103220172", json.dumps(items_data),
                    14400.00, 3512.00, 272.20, 272.20, 11432.00, 0.0, 11432.00,
                    "Credit", "posted", now_iso()
                )
            )
            print(f"Purchase invoice {inv_no} inserted successfully!")
        else:
            print(f"Invoice {inv_no} already exists.")

if __name__ == "__main__":
    asyncio.run(add_stanes_invoice())
