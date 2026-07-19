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

async def insert_svs_rava_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding SVS Agri & Rava Chemicals Invoices for ADMIN user ({owner_id})...")

    # Supplier 1: SVS AGRI SOLUTIONS
    sup_svs = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("SVS AGRI SOLUTIONS (DHANUKA)", owner_id))
    if not sup_svs:
        sup_svs_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_svs_id, "SVS AGRI SOLUTIONS (DHANUKA)", "DHANUKA AGRITECH LTD", "9676777711", "agrisolutions.svs@gmail.com",
             "#17-65, Behind Old Town Post Office, Gooty Road, Anantapuramu - 515001 AP", "37BVZPS4763H1ZJ", 167395.00, owner_id, now_iso())
        )
    else:
        sup_svs_id = sup_svs["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 167395.00 WHERE id = ?", (sup_svs_id,))

    # Supplier 2: RAVA AGRI CHEMICALS PVT LTD
    sup_rava = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("RAVA AGRI CHEMICALS PVT LTD", owner_id))
    if not sup_rava:
        sup_rava_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "RAVA AGRI CHEMICALS PVT LTD", "9246927366", "rac@ariesagro.com",
             "D.No:15-44, Sai Nagar Venture, Rajeev Colony, Gooty Road, Anantapuramu - 515001 AP", "37AAECR5394P1ZI", 16473.00, owner_id, now_iso())
        )
    else:
        sup_rava_id = sup_rava["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 16473.00 WHERE id = ?", (sup_rava_id,))

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
             f"89030395{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- SVS INVOICE: SVSG/26-27/30 (19-05-2026) ----------------
    p_cur500 = await get_or_create_prod("CURACRON 50 EC 500 ML", "Pesticides", "Bottle", 398.70, 440.00, "SBS6C2W130", "2028-03-15", "SVS AGRI SOLUTIONS")
    p_cur250 = await get_or_create_prod("CURACRON 50 EC 250 ML", "Pesticides", "Bottle", 207.00, 230.00, "SBS6A2W044", "2028-01-20", "SVS AGRI SOLUTIONS")
    p_kar500 = await get_or_create_prod("KARATE 500 ML", "Pesticides", "Bottle", 362.00, 400.00, "SBS5J2W271", "2027-10-10", "SVS AGRI SOLUTIONS")
    p_kar250 = await get_or_create_prod("KARATE 250 ML", "Pesticides", "Bottle", 168.30, 190.00, "SBS5G2W167", "2027-07-10", "SVS AGRI SOLUTIONS")
    p_snail = await get_or_create_prod("SNAILKILL 1 KG", "Pesticides", "Packet", 1090.73, 1200.00, "25SNV136-3", "2027-11-27", "SVS AGRI SOLUTIONS")
    p_sak150 = await get_or_create_prod("Sakura 10% EC 150ml", "Pesticides", "Bottle", 329.43, 370.00, "SKR0526", "2028-05-19", "SVS AGRI SOLUTIONS")
    p_sim240 = await get_or_create_prod("SIMODIS 240 ML", "Pesticides", "Bottle", 2025.86, 2250.00, "SIM0526", "2028-05-19", "SVS AGRI SOLUTIONS")
    p_sim120 = await get_or_create_prod("SIMODIS 120 ML", "Pesticides", "Bottle", 1042.69, 1160.00, "SIM0526", "2028-05-19", "SVS AGRI SOLUTIONS")
    p_ali200 = await get_or_create_prod("ALIKA 200 ML", "Pesticides", "Bottle", 464.10, 510.00, "ALK0526", "2028-05-19", "SVS AGRI SOLUTIONS")
    p_rido250 = await get_or_create_prod("RIDOMIL GOLD MZ 68 WP 250 G", "Fungicides", "Packet", 387.90, 430.00, "SPL6820042", "2028-02-13", "SVS AGRI SOLUTIONS")
    p_rido500 = await get_or_create_prod("RIDOMIL GOLD MZ 68 WP 500 G", "Fungicides", "Packet", 748.49, 830.00, "SPL5L20483", "2027-12-08", "SVS AGRI SOLUTIONS")
    p_kav400 = await get_or_create_prod("KAVACH FLO 400 ML", "Fungicides", "Bottle", 652.51, 720.00, "SPL5I20030", "2027-09-21", "SVS AGRI SOLUTIONS")
    p_peg500 = await get_or_create_prod("PEGASUS 50 WP 500 GMS", "Pesticides", "Packet", 1577.70, 1750.00, "SPL5L20232", "2027-09-20", "SVS AGRI SOLUTIONS")
    p_cur1 = await get_or_create_prod("CURACRON 50 EC 1 L", "Pesticides", "Bottle", 767.70, 850.00, "SBS5K2W376", "2027-11-09", "SVS AGRI SOLUTIONS")

    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_cur500,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_cur250,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_kar500,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_kar250,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_snail,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_sak150,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_sim240,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_sim120,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_ali200,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_rido250,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_rido500,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_kav400,))
    await execute("UPDATE products SET current_stock = current_stock + 8 WHERE id = ?", (p_peg500,))
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_cur1,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SVSG/26-27/30", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_cur500, "product_name": "CURACRON 50 EC 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 337.88, "amount": 6757.60, "batch_number": "SBS6C2W130", "expiry_date": "2028-03-15"},
            {"product_id": p_cur250, "product_name": "CURACRON 50 EC 250 ML", "unit": "Bottle", "qty": 40.0, "unit_price": 175.42, "amount": 7016.80, "batch_number": "SBS6A2W044", "expiry_date": "2028-01-20"},
            {"product_id": p_kar500, "product_name": "KARATE 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 306.78, "amount": 6135.60, "batch_number": "SBS5J2W271", "expiry_date": "2027-10-10"},
            {"product_id": p_kar250, "product_name": "KARATE 250 ML", "unit": "Bottle", "qty": 40.0, "unit_price": 142.63, "amount": 5705.20, "batch_number": "SBS5G2W167", "expiry_date": "2027-07-10"},
            {"product_id": p_snail, "product_name": "SNAILKILL 1 KG", "unit": "Packet", "qty": 10.0, "unit_price": 924.35, "amount": 9243.50, "batch_number": "25SNV136-3", "expiry_date": "2027-11-27"},
            {"product_id": p_sak150, "product_name": "Sakura 10% EC 150ml", "unit": "Bottle", "qty": 40.0, "unit_price": 279.18, "amount": 11167.20, "batch_number": "SKR0526", "expiry_date": "2028-05-19"},
            {"product_id": p_sim240, "product_name": "SIMODIS 240 ML", "unit": "Bottle", "qty": 10.0, "unit_price": 1716.83, "amount": 17168.30, "batch_number": "SIM0526", "expiry_date": "2028-05-19"},
            {"product_id": p_sim120, "product_name": "SIMODIS 120 ML", "unit": "Bottle", "qty": 10.0, "unit_price": 883.64, "amount": 8836.40, "batch_number": "SIM0526", "expiry_date": "2028-05-19"},
            {"product_id": p_ali200, "product_name": "ALIKA 200 ML", "unit": "Bottle", "qty": 40.0, "unit_price": 393.30, "amount": 15732.00, "batch_number": "ALK0526", "expiry_date": "2028-05-19"},
            {"product_id": p_rido250, "product_name": "RIDOMIL GOLD MZ 68 WP 250 G", "unit": "Packet", "qty": 40.0, "unit_price": 328.73, "amount": 13149.20, "batch_number": "SPL6820042", "expiry_date": "2028-02-13"},
            {"product_id": p_rido500, "product_name": "RIDOMIL GOLD MZ 68 WP 500 G", "unit": "Packet", "qty": 20.0, "unit_price": 634.31, "amount": 12686.20, "batch_number": "SPL5L20483", "expiry_date": "2027-12-08"},
            {"product_id": p_kav400, "product_name": "KAVACH FLO 400 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 552.98, "amount": 11059.60, "batch_number": "SPL5I20030", "expiry_date": "2027-09-21"},
            {"product_id": p_peg500, "product_name": "PEGASUS 50 WP 500 GMS", "unit": "Packet", "qty": 8.0, "unit_price": 1337.04, "amount": 10696.32, "batch_number": "SPL5L20232", "expiry_date": "2027-09-20"},
            {"product_id": p_cur1, "product_name": "CURACRON 50 EC 1 L", "unit": "Bottle", "qty": 10.0, "unit_price": 650.59, "amount": 6505.90, "batch_number": "SBS5K2W376", "expiry_date": "2027-11-09"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_svs_id, "SVS AGRI SOLUTIONS (DHANUKA)", "SVSG/26-27/30", "2026-05-19", "Main Warehouse", "BY AUTO", "Credit", "2026-05-19",
             "Scanned SVS Invoice SVSG/26-27/30", json.dumps(items1), 141874.22, 0.0, 12760.39, 12760.39, 167395.00, 0.0, 167395.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- RAVA INVOICE: F/26-27/1632 (09-07-2026) ----------------
    p_aripot1 = await get_or_create_prod("ARIPOTASH 1 LT", "Bio-Fertilizers", "Bottle", 852.71, 950.00, "M016", "2028-06-30", "RAVA AGRI CHEMICALS PVT LTD")
    p_aripot5 = await get_or_create_prod("ARIPOTASH 5 LT CAN", "Bio-Fertilizers", "Can", 3711.56, 4000.00, "M009", "2028-04-30", "RAVA AGRI CHEMICALS PVT LTD")
    p_aquacal5 = await get_or_create_prod("AQUACAL 5 LT", "Bio-Fertilizers", "Can", 1887.76, 2100.00, "M043", "2028-06-30", "RAVA AGRI CHEMICALS PVT LTD")

    await execute("UPDATE products SET current_stock = current_stock + 12 WHERE id = ?", (p_aripot1,))
    await execute("UPDATE products SET current_stock = current_stock + 2 WHERE id = ?", (p_aripot5,))
    await execute("UPDATE products SET current_stock = current_stock + 2 WHERE id = ?", (p_aquacal5,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("F/26-27/1632", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_aripot1, "product_name": "ARIPOTASH 1 LT", "unit": "Bottle", "qty": 12.0, "unit_price": 787.34, "amount": 9448.08, "batch_number": "M016", "expiry_date": "2028-06-30"},
            {"product_id": p_aripot5, "product_name": "ARIPOTASH 5 LT CAN", "unit": "Can", "qty": 2.0, "unit_price": 3534.82, "amount": 7069.64, "batch_number": "M009", "expiry_date": "2028-04-30"},
            {"product_id": p_aquacal5, "product_name": "AQUACAL 5 LT", "unit": "Can", "qty": 2.0, "unit_price": 1797.87, "amount": 3595.74, "batch_number": "M043", "expiry_date": "2028-06-30"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_rava_id, "RAVA AGRI CHEMICALS PVT LTD", "F/26-27/1632", "2026-07-09", "Main Warehouse", "G.VEERANJANEYULU", "Credit", "2026-07-09",
             "Scanned Rava Invoice F/26-27/1632", json.dumps(items2), 20113.46, 4425.00, 392.22, 392.22, 16473.00, 0.0, 16473.00, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added SVS Agri & Rava Chemicals invoices into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_svs_rava_admin())
