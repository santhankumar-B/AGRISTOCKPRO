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

async def insert_4_nova_july21_set5_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding 4 Nova Invoices (July 21 Set 5) for ADMIN user ({owner_id})...")

    # Supplier: NOVA AGRITECH LIMITED
    sup_nova_tech = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("NOVA AGRITECH LIMITED", owner_id))
    if not sup_nova_tech:
        sup_nova_tech_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_nova_tech_id, "NOVA AGRITECH LIMITED", "NOVA AGRITECH LIMITED", "7995084789", "accounts@novaagri.in",
             "Sy No 251/A, Singannaguda Village, Mulugu Mandal Siddipet, TG - 502279", "36AACCN8771A2ZH", 117956.52, owner_id, now_iso())
        )
    else:
        sup_nova_tech_id = sup_nova_tech["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 117956.52 WHERE id = ?", (sup_nova_tech_id,))

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
             f"89030406{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- 1. NOVA AGRITECH: 126273601167 (29-06-2026) ----------------
    p_lava_double = await get_or_create_prod("Super Lava Double Jodi-250 ML", "Pesticides", "Bottle", 1400.04, 1550.00, "N26004", "2029-01-02", "NOVA AGRITECH LIMITED")
    await execute("UPDATE products SET current_stock = current_stock + 16 WHERE id = ?", (p_lava_double,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("126273601167", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_lava_double, "product_name": "Super Lava Double Jodi-250 ML", "unit": "Bottle", "qty": 16.0, "unit_price": 1333.37, "amount": 21333.94, "batch_number": "N26004", "expiry_date": "2029-01-02"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_tech_id, "NOVA AGRITECH LIMITED", "126273601167", "2026-06-29", "Main Warehouse", "Mangala Goods", "Credit", "2026-06-29",
             "Scanned Nova Invoice 126273601167", json.dumps(items1), 21333.94, 0.0, 533.35, 533.35, 22400.64, 0.0, 22400.64, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 2. NOVA AGRITECH: 126273600413 (03-06-2026) ----------------
    p_nutri_bond = await get_or_create_prod("Nova Nutri Bond 25 Kg", "Fertilizers", "Bag", 4525.28, 4900.00, "N26003", "2029-05-10", "NOVA AGRITECH LIMITED")
    p_nova2828 = await get_or_create_prod("Nova Fert 2828 25 Kg", "Fertilizers", "Bag", 3725.23, 4100.00, "N26003", "2029-05-27", "NOVA AGRITECH LIMITED")

    await execute("UPDATE products SET current_stock = current_stock + 2 WHERE id = ?", (p_nutri_bond,))
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_nova2828,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("126273600413", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_nutri_bond, "product_name": "Nova Nutri Bond 25 Kg", "unit": "Bag", "qty": 2.0, "unit_price": 4309.79, "amount": 8619.58, "batch_number": "N26003", "expiry_date": "2029-05-10"},
            {"product_id": p_nova2828, "product_name": "Nova Fert 2828 25 Kg", "unit": "Bag", "qty": 5.0, "unit_price": 3547.83, "amount": 17739.17, "batch_number": "N26003", "expiry_date": "2029-05-27"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_tech_id, "NOVA AGRITECH LIMITED", "126273600413", "2026-06-03", "Main Warehouse", "Mangala Goods", "Credit", "2026-06-03",
             "Scanned Nova Invoice 126273600413", json.dumps(items2), 26358.75, 0.0, 658.97, 658.97, 27676.69, 0.0, 27676.69, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 3. NOVA AGRITECH: 126273600815 (19-06-2026) ----------------
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_nutri_bond,))

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("126273600815", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_nutri_bond, "product_name": "Nova Nutri Bond 25 Kg", "unit": "Bag", "qty": 10.0, "unit_price": 4309.79, "amount": 43097.90, "batch_number": "N26006", "expiry_date": "2029-06-18"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_tech_id, "NOVA AGRITECH LIMITED", "126273600815", "2026-06-19", "Main Warehouse", "Mangala Goods", "Credit", "2026-06-19",
             "Scanned Nova Invoice 126273600815", json.dumps(items3), 43097.90, 0.0, 1077.44, 1077.44, 45252.79, 0.0, 45252.79, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 4. NOVA AGRITECH: 126273600814 (19-06-2026) ----------------
    await execute("UPDATE products SET current_stock = current_stock + 5 WHERE id = ?", (p_nutri_bond,))

    inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("126273600814", owner_id))
    if not inv4:
        items4 = [
            {"product_id": p_nutri_bond, "product_name": "Nova Nutri Bond 25 Kg", "unit": "Bag", "qty": 5.0, "unit_price": 4309.79, "amount": 21548.95, "batch_number": "N26006", "expiry_date": "2029-06-18"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_nova_tech_id, "NOVA AGRITECH LIMITED", "126273600814", "2026-06-19", "Main Warehouse", "Mangala Goods", "Credit", "2026-06-19",
             "Scanned Nova Invoice 126273600814", json.dumps(items4), 21548.95, 0.0, 538.72, 538.72, 22626.40, 0.0, 22626.40, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added 4 Nova Invoices (July 21 Set 5) into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_4_nova_july21_set5_admin())
