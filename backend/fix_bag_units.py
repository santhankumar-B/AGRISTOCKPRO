import asyncio
import os
import sys
import json
from datetime import datetime, timezone

sys.path.append(os.path.dirname(__file__))
from database import init_db, fetch_one, fetch_all, execute

async def fix_units():
    init_db()
    users = await fetch_all("SELECT * FROM users")
    
    for user in users:
        owner_id = user["id"]
        username = user["username"]
        print(f"Fixing bag units for user: {username} ({owner_id})...")

        # 1. Update ADDON product
        p1_name = "ADDON (NPK-19-19-19) 25KG"
        existing_p1 = await fetch_one("SELECT * FROM products WHERE name = ? AND owner_id = ?", (p1_name, owner_id))
        if existing_p1:
            await execute(
                """UPDATE products SET 
                    unit = 'Bag',
                    current_stock = 5.0,
                    purchase_price = 3045.00,
                    selling_price = 3105.00
                WHERE id = ? AND owner_id = ?""",
                (existing_p1["id"], owner_id)
            )

        # 2. Update HUGO product
        p2_name = "HUGO (POTASSIUM NITRATE) 1KG"
        existing_p2 = await fetch_one("SELECT * FROM products WHERE name = ? AND owner_id = ?", (p2_name, owner_id))
        if existing_p2:
            await execute(
                """UPDATE products SET 
                    unit = 'Packet',
                    current_stock = 25.0,
                    purchase_price = 142.60,
                    selling_price = 335.00
                WHERE id = ? AND owner_id = ?""",
                (existing_p2["id"], owner_id)
            )

        # 3. Update Purchase invoice 303101220021 items_json
        inv_no = "303101220021"
        pur = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", (inv_no, owner_id))
        if pur:
            p1_id = existing_p1["id"] if existing_p1 else ""
            p2_id = existing_p2["id"] if existing_p2 else ""
            items_data = [
                {
                    "product_id": p1_id,
                    "product_name": p1_name,
                    "unit": "Bag",
                    "qty": 5.0,
                    "unit_price": 3045.00,
                    "amount": 15225.00,
                    "batch_number": "1919190426",
                    "expiry_date": "2030-04-29"
                },
                {
                    "product_id": p2_id,
                    "product_name": p2_name,
                    "unit": "Packet",
                    "qty": 25.0,
                    "unit_price": 142.60,
                    "amount": 3565.00,
                    "batch_number": "TS/PN/0426",
                    "expiry_date": "2030-04-29"
                }
            ]
            await execute(
                "UPDATE purchases SET items_json = ? WHERE id = ? AND owner_id = ?",
                (json.dumps(items_data), pur["id"], owner_id)
            )
            print(f"Updated purchase invoice {inv_no} items with Bag/Packet units!")

if __name__ == "__main__":
    asyncio.run(fix_units())
