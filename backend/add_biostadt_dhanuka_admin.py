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

async def insert_biostadt_dhanuka_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding 5 Biostadt & Dhanuka Invoices for ADMIN user ({owner_id})...")

    # Supplier 1: BIOSTADT INDIA LIMITED
    sup_bio = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("BIOSTADT INDIA LIMITED", owner_id))
    if not sup_bio:
        sup_bio_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_bio_id, "BIOSTADT INDIA LIMITED", "BIOSTADT INDIA LIMITED", "912266520520", "supplychain@biostadt.com",
             "Biostadt India Ltd Kurnool CSC Location, Survey No.194&189, Peddapadu village Bellary Road, Kallur, Kurnool 518003 AP", "37ACCB1830G1ZZ", 105458.97, owner_id, now_iso())
        )
    else:
        sup_bio_id = sup_bio["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 105458.97 WHERE id = ?", (sup_bio_id,))

    # Supplier 2: SVS AGRI SOLUTIONS (DHANUKA)
    sup_dha = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("SVS AGRI SOLUTIONS (DHANUKA)", owner_id))
    if not sup_dha:
        sup_dha_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_dha_id, "SVS AGRI SOLUTIONS (DHANUKA)", "DHANUKA AGRITECH LTD", "9676777711", "agrisolutions.svs@gmail.com",
             "#17-65, Behind Old Town Post Office, Gooty Road, Anantapuramu - 515001 AP", "37BVZPS4763H1ZJ", 160490.00, owner_id, now_iso())
        )
    else:
        sup_dha_id = sup_dha["id"]
        await execute("UPDATE suppliers SET outstanding_amount = outstanding_amount + 160490.00 WHERE id = ?", (sup_dha_id,))

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
             f"89030390{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- BIOSTADT INVOICE 1: 9112253223 (29.06.2026) ----------------
    p_cyg = await get_or_create_prod("CYGNET 10WP 100 GM", "Pesticides", "Packet", 105.02, 120.00, "JC26PA002", "2028-01-15", "BIOSTADT INDIA LIMITED")
    p_stop250 = await get_or_create_prod("STOP 13EC 250 ML", "Pesticides", "Bottle", 119.18, 135.00, "WQR25L08", "2027-12-17", "BIOSTADT INDIA LIMITED")
    p_stop500 = await get_or_create_prod("STOP 13EC 500 ML", "Pesticides", "Bottle", 220.66, 250.00, "WQR25L023", "2028-05-09", "BIOSTADT INDIA LIMITED")
    p_ult250 = await get_or_create_prod("ULTIMO 250 ML", "Pesticides", "Bottle", 276.71, 310.00, "JU026L0023", "2028-04-21", "BIOSTADT INDIA LIMITED")

    await execute("UPDATE products SET current_stock = current_stock + 80 WHERE id = ?", (p_cyg,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_stop250,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_stop500,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_ult250,))

    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("9112253223", owner_id))
    if not inv1:
        items1 = [
            {"product_id": p_cyg, "product_name": "CYGNET 10WP 100 GM", "unit": "Packet", "qty": 80.0, "unit_price": 89.00, "amount": 7120.00, "batch_number": "JC26PA002", "expiry_date": "2028-01-15"},
            {"product_id": p_stop250, "product_name": "STOP 13EC 250 ML", "unit": "Bottle", "qty": 40.0, "unit_price": 101.00, "amount": 4040.00, "batch_number": "WQR25L08", "expiry_date": "2027-12-17"},
            {"product_id": p_stop500, "product_name": "STOP 13EC 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 187.00, "amount": 3740.00, "batch_number": "WQR25L023", "expiry_date": "2028-05-09"},
            {"product_id": p_ult250, "product_name": "ULTIMO 250 ML", "unit": "Bottle", "qty": 40.0, "unit_price": 234.50, "amount": 9380.00, "batch_number": "JU026L0023", "expiry_date": "2028-04-21"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_bio_id, "BIOSTADT INDIA LIMITED", "9112253223", "2026-06-29", "Main Warehouse", "KRANTI TRANSPORT", "Credit", "2026-06-29",
             "Scanned Biostadt Invoice 9112253223", json.dumps(items1), 24280.00, 0.0, 2185.20, 2185.20, 28650.40, 0.0, 28650.40, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- BIOSTADT INVOICE 2: 9112253224 (29.06.2026) ----------------
    p_biogreen = await get_or_create_prod("BioGreen Calcium 1 LIT", "Bio-Fertilizers", "Bottle", 577.50, 640.00, "BGC26LA002", "2029-01-26", "BIOSTADT INDIA LIMITED")
    await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_biogreen,))

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("9112253224", owner_id))
    if not inv2:
        items2 = [
            {"product_id": p_biogreen, "product_name": "BioGreen Calcium 1 LIT", "unit": "Bottle", "qty": 10.0, "unit_price": 550.00, "amount": 5500.00, "batch_number": "BGC26LA002", "expiry_date": "2029-01-26"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_bio_id, "BIOSTADT INDIA LIMITED", "9112253224", "2026-06-29", "Main Warehouse", "KRANTI TRANSPORT", "Credit", "2026-06-29",
             "Scanned Biostadt Invoice 9112253224", json.dumps(items2), 5500.00, 0.0, 137.50, 137.50, 5775.00, 0.0, 5775.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- BIOSTADT INVOICE 3: 9112253012 (12.06.2026) ----------------
    p_4in1 = await get_or_create_prod("4 IN 1 - 250 GM", "Pesticides", "Packet", 87.32, 100.00, "B4126L026", "2028-05-28", "BIOSTADT INDIA LIMITED")
    p_stop10ec = await get_or_create_prod("STOP 10EC 500 ML", "Pesticides", "Bottle", 220.66, 250.00, "WSR26L022", "2028-05-05", "BIOSTADT INDIA LIMITED")
    p_klin = await get_or_create_prod("KLINTOP 10% EC 500 ML", "Pesticides", "Bottle", 400.02, 450.00, "JKP25LH012", "2027-05-23", "BIOSTADT INDIA LIMITED")
    p_jaan = await get_or_create_prod("JAANBAZ 5% SC 500 ML", "Pesticides", "Bottle", 383.50, 430.00, "JJ26L001", "2028-05-11", "BIOSTADT INDIA LIMITED")
    p_dart = await get_or_create_prod("DARTRIZ 50SP 250 GM", "Pesticides", "Packet", 381.73, 430.00, "JDC26PC003", "2028-03-20", "BIOSTADT INDIA LIMITED")
    p_hit = await get_or_create_prod("HITBAC 38.7% 700 ML", "Pesticides", "Bottle", 453.12, 510.00, "JHY26L013", "2028-05-18", "BIOSTADT INDIA LIMITED")
    p_trig = await get_or_create_prod("TRIGGER PRO 500 ML", "Pesticides", "Bottle", 125.08, 145.00, "JTA26L005", "2028-01-30", "BIOSTADT INDIA LIMITED")

    await execute("UPDATE products SET current_stock = current_stock + 80 WHERE id = ?", (p_4in1,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_stop10ec,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_klin,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_jaan,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_dart,))
    await execute("UPDATE products SET current_stock = current_stock + 30 WHERE id = ?", (p_hit,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_trig,))

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("9112253012", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_4in1, "product_name": "4 IN 1 - 250 GM", "unit": "Packet", "qty": 80.0, "unit_price": 74.00, "amount": 5920.00, "batch_number": "B4126L026", "expiry_date": "2028-05-28"},
            {"product_id": p_stop10ec, "product_name": "STOP 10EC 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 187.00, "amount": 3740.00, "batch_number": "WSR26L022", "expiry_date": "2028-05-05"},
            {"product_id": p_klin, "product_name": "KLINTOP 10% EC 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 339.00, "amount": 6780.00, "batch_number": "JKP25LH012", "expiry_date": "2027-05-23"},
            {"product_id": p_jaan, "product_name": "JAANBAZ 5% SC 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 325.00, "amount": 6500.00, "batch_number": "JJ26L001", "expiry_date": "2028-05-11"},
            {"product_id": p_dart, "product_name": "DARTRIZ 50SP 250 GM", "unit": "Packet", "qty": 40.0, "unit_price": 323.50, "amount": 12940.00, "batch_number": "JDC26PC003", "expiry_date": "2028-03-20"},
            {"product_id": p_hit, "product_name": "HITBAC 38.7% 700 ML", "unit": "Bottle", "qty": 30.0, "unit_price": 384.00, "amount": 11519.97, "batch_number": "JHY26L013", "expiry_date": "2028-05-18"},
            {"product_id": p_trig, "product_name": "TRIGGER PRO 500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 106.00, "amount": 2120.00, "batch_number": "JTA26L005", "expiry_date": "2028-01-30"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_bio_id, "BIOSTADT INDIA LIMITED", "9112253012", "2026-06-12", "Main Warehouse", "Direct", "Credit", "2026-06-12",
             "Scanned Biostadt Invoice 9112253012", json.dumps(items3), 49519.97, 0.0, 4456.80, 4456.80, 58433.57, 0.0, 58433.57, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- BIOSTADT INVOICE 4: 9112253013 (12.06.2026) ----------------
    p_bioz = await get_or_create_prod("BIOZYME GRANULES 8 KG", "Bio-Fertilizers", "Bag", 420.00, 460.00, "BBG26G002", "2029-04-13", "BIOSTADT INDIA LIMITED")
    await execute("UPDATE products SET current_stock = current_stock + 30 WHERE id = ?", (p_bioz,))

    inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("9112253013", owner_id))
    if not inv4:
        items4 = [
            {"product_id": p_bioz, "product_name": "BIOZYME GRANULES 8 KG", "unit": "Bag", "qty": 30.0, "unit_price": 400.00, "amount": 12000.00, "batch_number": "BBG26G002", "expiry_date": "2029-04-13"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_bio_id, "BIOSTADT INDIA LIMITED", "9112253013", "2026-06-12", "Main Warehouse", "Direct", "Credit", "2026-06-12",
             "Scanned Biostadt Invoice 9112253013", json.dumps(items4), 12000.00, 0.0, 300.00, 300.00, 12600.00, 0.0, 12600.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- DHANUKA INVOICE 5: SVSGTY26-27/28 (22-05-2026) ----------------
    p_targa = await get_or_create_prod("Targa Super 5% EC 20X500 ML", "Pesticides", "Bottle", 780.00, 850.00, "TS5EC0526", "2028-05-22", "DHANUKA AGRITECH LTD")
    p_sempra = await get_or_create_prod("Sempra 75% WG 24X36gms", "Pesticides", "Packet", 1290.00, 1400.00, "KDQ-0152", "2027-07-31", "DHANUKA AGRITECH LTD")
    p_sakura = await get_or_create_prod("SAKURA 40X150 ML", "Pesticides", "Bottle", 338.00, 380.00, "SKR0526", "2028-05-22", "DHANUKA AGRITECH LTD")
    p_barrier = await get_or_create_prod("Barrier 70% WP 40X250 GMS", "Pesticides", "Packet", 360.00, 400.00, "BAR0526", "2028-05-22", "DHANUKA AGRITECH LTD")
    p_kasub = await get_or_create_prod("Kasu-B 3L 20X500 ML", "Fungicides", "Bottle", 510.00, 570.00, "KAS0526", "2028-05-22", "DHANUKA AGRITECH LTD")
    p_mortar = await get_or_create_prod("Mortar 75% SG 40X250 GMS", "Pesticides", "Packet", 930.00, 1020.00, "MOR0526", "2028-05-22", "DHANUKA AGRITECH LTD")
    p_niss120 = await get_or_create_prod("NISSODIUM 5% 32X120 ML", "Fungicides", "Bottle", 960.00, 1050.00, "NIS0526", "2028-05-22", "DHANUKA AGRITECH LTD")
    p_niss200 = await get_or_create_prod("NISSODIUM 30X200 ML", "Fungicides", "Bottle", 1550.00, 1700.00, "NIS0526", "2028-05-22", "DHANUKA AGRITECH LTD")

    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_targa,))
    await execute("UPDATE products SET current_stock = current_stock + 24 WHERE id = ?", (p_sempra,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_sakura,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_barrier,))
    await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_kasub,))
    await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_mortar,))
    await execute("UPDATE products SET current_stock = current_stock + 16 WHERE id = ?", (p_niss120,))
    await execute("UPDATE products SET current_stock = current_stock + 15 WHERE id = ?", (p_niss200,))

    inv5 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SVSGTY26-27/28", owner_id))
    if not inv5:
        items5 = [
            {"product_id": p_targa, "product_name": "Targa Super 5% EC 20X500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 661.02, "amount": 13220.34, "batch_number": "TS5EC0526", "expiry_date": "2028-05-22"},
            {"product_id": p_sempra, "product_name": "Sempra 75% WG 24X36gms", "unit": "Packet", "qty": 24.0, "unit_price": 1093.22, "amount": 26237.28, "batch_number": "KDQ-0152", "expiry_date": "2027-07-31"},
            {"product_id": p_sakura, "product_name": "SAKURA 40X150 ML", "unit": "Bottle", "qty": 40.0, "unit_price": 286.44, "amount": 11457.62, "batch_number": "SKR0526", "expiry_date": "2028-05-22"},
            {"product_id": p_barrier, "product_name": "Barrier 70% WP 40X250 GMS", "unit": "Packet", "qty": 40.0, "unit_price": 305.08, "amount": 12203.38, "batch_number": "BAR0526", "expiry_date": "2028-05-22"},
            {"product_id": p_kasub, "product_name": "Kasu-B 3L 20X500 ML", "unit": "Bottle", "qty": 20.0, "unit_price": 432.20, "amount": 8644.06, "batch_number": "KAS0526", "expiry_date": "2028-05-22"},
            {"product_id": p_mortar, "product_name": "Mortar 75% SG 40X250 GMS", "unit": "Packet", "qty": 40.0, "unit_price": 788.14, "amount": 31525.60, "batch_number": "MOR0526", "expiry_date": "2028-05-22"},
            {"product_id": p_niss120, "product_name": "NISSODIUM 5% 32X120 ML", "unit": "Bottle", "qty": 16.0, "unit_price": 813.56, "amount": 13016.94, "batch_number": "NIS0526", "expiry_date": "2028-05-22"},
            {"product_id": p_niss200, "product_name": "NISSODIUM 30X200 ML", "unit": "Bottle", "qty": 15.0, "unit_price": 1313.56, "amount": 19703.38, "batch_number": "NIS0526", "expiry_date": "2028-05-22"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_dha_id, "SVS AGRI SOLUTIONS (DHANUKA)", "SVSGTY26-27/28", "2026-05-22", "Main Warehouse", "BY AUTO", "Credit", "2026-05-22",
             "Scanned SVS Dhanuka Invoice SVSGTY26-27/28", json.dumps(items5), 136008.42, 0.0, 12240.79, 12240.79, 160490.00, 0.0, 160490.00, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added 5 Biostadt & Dhanuka invoices into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_biostadt_dhanuka_admin())
