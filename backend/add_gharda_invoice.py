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

async def insert_gharda_invoice_bottle_units():
    init_db()
    users = await fetch_all("SELECT * FROM users")
    if not users:
        print("No users found.")
        return

    for u in users:
        owner_id = u["id"]
        username = u["username"]
        print(f"Updating Gharda Chemicals Tax Invoice #4521601156 with bottle units for user: {username}...")

        # 1. Supplier: GHARDA CHEMICALS LIMITED
        sup = await fetch_one("SELECT * FROM suppliers WHERE name LIKE '%GHARDA%' AND owner_id = ?", (owner_id,))
        if not sup:
            sup_id = uid()
            await execute(
                """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sup_id, "GHARDA CHEMICALS LIMITED", "GHARDA CHEMICALS LIMITED", "9985373894", "gharda_knl@yahoo.com",
                 "Gharda Chemicals Ltd. (Kurnool) S NO 269,194,189, Bellary Road, Peddapadu (V), Kallur (M) Kurnool 518004", "37AAACG1255E1Z0", 97674.00, owner_id, now_iso())
            )
        else:
            sup_id = sup["id"]

        # Product items list with exact Bottle / Can units, converted quantities & bottle rates
        gharda_products = [
            {
                "name": "Deltamethrin 11% W/W Ec (Boxerr-250 ML)",
                "category": "Pesticides",
                "hsn": "38086900",
                "batch": "BOX25E0125",
                "expiry": "2027-11-14",
                "unit": "Bottle", # 250 ML Bottle
                "qty": 40.0,     # 10 Litres = 40 Bottles of 250 ML
                "unit_price": 355.95, # Rate/4 (1,423.80 / 4)
                "selling_price": 400.00,
                "amount": 14238.00
            },
            {
                "name": "Deltamethrin 11% W/W Ec (Boxerr-500 ML)",
                "category": "Pesticides",
                "hsn": "38086900",
                "batch": "BOX26E0129",
                "expiry": "2028-04-10",
                "unit": "Bottle", # 500 ML Bottle
                "qty": 20.0,     # 10 Litres = 20 Bottles of 500 ML
                "unit_price": 704.70, # Rate/2 (1,409.40 / 2)
                "selling_price": 780.00,
                "amount": 14094.00
            },
            {
                "name": "Chlorpyrifos 50% + Cypermethrin 5% Ec (HAMLA 550-1 LTR)",
                "category": "Pesticides",
                "hsn": "38089199",
                "batch": "HML26E3342",
                "expiry": "2028-04-19",
                "unit": "Bottle", # 1 LTR Bottle
                "qty": 10.0,     # 10 Litres = 10 Bottles of 1 LTR
                "unit_price": 581.40,
                "selling_price": 680.00,
                "amount": 5814.00
            },
            {
                "name": "Chlorpyrifos 50% + Cypermethrin 5% Ec (HAMLA 550-500 ML)",
                "category": "Pesticides",
                "hsn": "38089199",
                "batch": "HML25E3264",
                "expiry": "2027-07-02",
                "unit": "Bottle", # 500 ML Bottle
                "qty": 20.0,     # 10 Litres = 20 Bottles of 500 ML
                "unit_price": 297.90, # Rate/2 (595.80 / 2)
                "selling_price": 350.00,
                "amount": 5958.00
            },
            {
                "name": "Chlorpyrifos 50% Ec (Ecoguard-1 LTR)",
                "category": "Pesticides",
                "hsn": "38089199",
                "batch": "ECO26E4586",
                "expiry": "2028-04-11",
                "unit": "Bottle", # 1 LTR Bottle
                "qty": 20.0,     # 20 Litres = 20 Bottles of 1 LTR
                "unit_price": 494.10,
                "selling_price": 560.00,
                "amount": 9882.00
            },
            {
                "name": "Indoxacarb 14.5% + Acetamiprid 7.7% W/W Sc (Kite-250 ML)",
                "category": "Pesticides",
                "hsn": "38089199",
                "batch": "KIT25J0113",
                "expiry": "2027-10-09",
                "unit": "Bottle", # 250 ML Bottle
                "qty": 40.0,     # 10 Litres = 40 Bottles of 250 ML
                "unit_price": 694.80, # Rate/4 (2,779.20 / 4)
                "selling_price": 780.00,
                "amount": 27792.00
            },
            {
                "name": "Profenofos 40% + Cypermethrin 4% Ec (Jugaad-1 LTR)",
                "category": "Pesticides",
                "hsn": "38089199",
                "batch": "PCM26E0206",
                "expiry": "2028-03-17",
                "unit": "Bottle", # 1 LTR Bottle
                "qty": 10.0,     # 10 Litres = 10 Bottles of 1 LTR
                "unit_price": 500.00,
                "selling_price": 580.00,
                "amount": 5000.00
            }
        ]

        purchase_items = []
        for gp in gharda_products:
            p_rec = await fetch_one("SELECT * FROM products WHERE name = ? AND owner_id = ?", (gp["name"], owner_id))
            if p_rec:
                pid = p_rec["id"]
                await execute(
                    """UPDATE products SET
                       unit = ?, current_stock = ?, purchase_price = ?, selling_price = ?, batch_number = ?, expiry_date = ?
                       WHERE id = ?""",
                    (gp["unit"], gp["qty"], gp["unit_price"], gp["selling_price"], gp["batch"], gp["expiry"], pid)
                )
            else:
                pid = uid()
                await execute(
                    """INSERT INTO products (id, name, category, company, brand, barcode, current_stock, minimum_stock, unit, purchase_price, selling_price, batch_number, expiry_date, owner_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (pid, gp["name"], gp["category"], "GHARDA CHEMICALS LIMITED", "GHARDA",
                     gp["hsn"], gp["qty"], 5.0, gp["unit"], gp["unit_price"], gp["selling_price"], gp["batch"], gp["expiry"], owner_id, now_iso())
                )

            purchase_items.append({
                "product_id": pid,
                "product_name": gp["name"],
                "unit": gp["unit"],
                "qty": gp["qty"],
                "unit_price": gp["unit_price"],
                "amount": gp["amount"],
                "batch_number": gp["batch"],
                "expiry_date": gp["expiry"]
            })

        # Update Purchase Invoice 4521601156
        inv = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("4521601156", owner_id))
        if inv:
            await execute(
                "UPDATE purchases SET items_json = ? WHERE id = ?",
                (json.dumps(purchase_items), inv["id"])
            )

    print("Gharda Chemicals Tax Invoice #4521601156 updated with bottle units & per-bottle prices successfully!")

if __name__ == "__main__":
    asyncio.run(insert_gharda_invoice_bottle_units())
