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

async def insert_5_slv_admin():
    init_db()
    
    # 1. Get admin user
    admin = await fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    if not admin:
        print("Admin user not found!")
        return

    owner_id = admin["id"]
    print(f"Adding ALL 5 SLV Agro Traders Invoices for ADMIN user ({owner_id})...")

    # Supplier: SRI LAKSHMI VENKATESWARA AGRO TRADERS
    sup_slv = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", ("SRI LAKSHMI VENKATESWARA AGRO TRADERS", owner_id))
    if not sup_slv:
        sup_slv_id = uid()
        await execute(
            """INSERT INTO suppliers (id, name, company, phone, email, address, gst, outstanding_amount, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "9490583999", "slvatcv@gmail.com",
             "Sy No: 71/1-1, Beside KTR Function Hall, Gooty Road, Anantapuramu AP", "37ADHPV2108G1ZJ", 426533.00, owner_id, now_iso())
        )
    else:
        sup_slv_id = sup_slv["id"]

    # Helper to get/create product for Admin
    async def get_or_create_prod(name, cat, unit, price, sell_price, batch, exp):
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
            (pid, name, cat, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SLVAT",
             f"89030401{int(uuid.uuid4().int) % 100000:05d}", 0.0, 2.0, unit, price, sell_price, batch, exp, owner_id, now_iso())
        )
        return pid

    # ---------------- 1. BILL #1: SLV/26-27/144 (20-04-2026) ----------------
    p_han200 = await get_or_create_prod("Hanabi 200Gms", "Pesticides", "Packet", 770.00, 850.00, "GJ0725004", "2027-07-28")
    
    inv1 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SLV/26-27/144", owner_id))
    if not inv1:
        await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_han200,))
        items1 = [
            {"product_id": p_han200, "product_name": "Hanabi 200Gms", "unit": "Packet", "qty": 40.0, "unit_price": 652.54, "amount": 26101.60, "batch_number": "GJ0725004", "expiry_date": "2027-07-28"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SLV/26-27/144", "2026-04-20", "Main Warehouse", "Direct", "Credit", "2026-04-20",
             "Scanned SLV Invoice SLV/26-27/144", json.dumps(items1), 26101.60, 0.0, 2349.14, 2349.14, 30800.00, 0.0, 30800.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 2. BILL #2: SLV/26-27/340 (08-05-2026) ----------------
    p_bar500 = await get_or_create_prod("Barazide 500Ml", "Pesticides", "Bottle", 960.00, 1080.00, "AINE506018", "2027-06-28")
    p_cab300 = await get_or_create_prod("Cabritop 300Gms", "Fungicides", "Packet", 699.00, 780.00, "ACT25165", "2026-07-20")
    p_aba100 = await get_or_create_prod("Abacin 100Ml", "Pesticides", "Bottle", 500.00, 560.00, "M-825/0235", "2026-07-20")
    p_sys100 = await get_or_create_prod("Systiva 100Ml", "Fungicides", "Bottle", 1025.00, 1150.00, "DSV26005M", "2028-01-06")
    p_exp34 = await get_or_create_prod("Exponus 34Ml", "Pesticides", "Bottle", 1350.00, 1500.00, "DEX25005", "2027-01-09")
    p_exp25 = await get_or_create_prod("Exponus 25Ml", "Pesticides", "Bottle", 1271.00, 1400.00, "DMEX26001", "2027-01-09")
    p_exp17 = await get_or_create_prod("Exponus 17Ml", "Pesticides", "Bottle", 821.00, 920.00, "DEX25005", "2027-01-09")
    p_pol40 = await get_or_create_prod("Police 40Gms", "Pesticides", "Packet", 380.00, 430.00, "PLC25J0455", "2027-10-03")
    p_eff280 = await get_or_create_prod("Efficon 280Ml", "Pesticides", "Bottle", 1361.00, 1500.00, "ADZ24016", "2026-07-27")
    p_lih500 = await get_or_create_prod("Lihocin 500Ml", "Bio-Fertilizers", "Bottle", 675.00, 750.00, "ALH25071", "2027-08-25")
    p_ace500 = await get_or_create_prod("Acemain 500Gms", "Pesticides", "Packet", 309.00, 350.00, "AIAC512559", "2027-12-18")

    inv2 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SLV/26-27/340", owner_id))
    if not inv2:
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_bar500,))
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_cab300,))
        await execute("UPDATE products SET current_stock = current_stock + 40 WHERE id = ?", (p_aba100,))
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_sys100,))
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_exp34,))
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_exp25,))
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_exp17,))
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_pol40,))
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_eff280,))
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_lih500,))
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_ace500,))
        items2 = [
            {"product_id": p_bar500, "product_name": "Barazide 500Ml", "unit": "Bottle", "qty": 10.0, "unit_price": 813.56, "amount": 8135.60, "batch_number": "AINE506018", "expiry_date": "2027-06-28"},
            {"product_id": p_cab300, "product_name": "Cabritop 300Gms", "unit": "Packet", "qty": 20.0, "unit_price": 592.37, "amount": 11847.40, "batch_number": "ACT25165", "expiry_date": "2026-07-20"},
            {"product_id": p_aba100, "product_name": "Abacin 100Ml", "unit": "Bottle", "qty": 40.0, "unit_price": 423.73, "amount": 16949.20, "batch_number": "M-825/0235", "expiry_date": "2026-07-20"},
            {"product_id": p_sys100, "product_name": "Systiva 100Ml", "unit": "Bottle", "qty": 20.0, "unit_price": 868.64, "amount": 17372.80, "batch_number": "DSV26005M", "expiry_date": "2028-01-06"},
            {"product_id": p_exp34, "product_name": "Exponus 34Ml", "unit": "Bottle", "qty": 10.0, "unit_price": 1144.07, "amount": 11440.70, "batch_number": "DEX25005", "expiry_date": "2027-01-09"},
            {"product_id": p_exp25, "product_name": "Exponus 25Ml", "unit": "Bottle", "qty": 10.0, "unit_price": 1077.12, "amount": 10771.20, "batch_number": "DMEX26001", "expiry_date": "2027-01-09"},
            {"product_id": p_exp17, "product_name": "Exponus 17Ml", "unit": "Bottle", "qty": 10.0, "unit_price": 695.76, "amount": 6957.60, "batch_number": "DEX25005", "expiry_date": "2027-01-09"},
            {"product_id": p_pol40, "product_name": "Police 40Gms", "unit": "Packet", "qty": 10.0, "unit_price": 322.03, "amount": 3220.30, "batch_number": "PLC25J0455", "expiry_date": "2027-10-03"},
            {"product_id": p_eff280, "product_name": "Efficon 280Ml", "unit": "Bottle", "qty": 10.0, "unit_price": 1153.39, "amount": 11533.90, "batch_number": "ADZ24016", "expiry_date": "2026-07-27"},
            {"product_id": p_lih500, "product_name": "Lihocin 500Ml", "unit": "Bottle", "qty": 20.0, "unit_price": 572.03, "amount": 11440.60, "batch_number": "ALH25071", "expiry_date": "2027-08-25"},
            {"product_id": p_ace500, "product_name": "Acemain 500Gms", "unit": "Packet", "qty": 20.0, "unit_price": 261.86, "amount": 5237.20, "batch_number": "AIAC512559", "expiry_date": "2027-12-18"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SLV/26-27/340", "2026-05-08", "Main Warehouse", "Direct", "Credit", "2026-05-08",
             "Scanned SLV Invoice SLV/26-27/340", json.dumps(items2), 114906.50, 0.0, 10341.59, 10341.59, 135589.68, 0.0, 135589.68, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 3. BILL #3: CREDIT NOTE / RETURN SR/26-27/34 (30-05-2026) ----------------
    p_koc1 = await get_or_create_prod("Kocide 1Kg", "Pesticides", "Packet", 1790.00, 1950.00, "25H3573VC4", "2027-05-04")
    p_sef400 = await get_or_create_prod("Sefina 400Ml", "Pesticides", "Bottle", 2065.00, 2250.00, "DSE26001", "2026-11-04")

    inv3 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SR/26-27/34", owner_id))
    if not inv3:
        items3 = [
            {"product_id": p_koc1, "product_name": "Kocide 1Kg", "unit": "Packet", "qty": 20.0, "unit_price": 1516.95, "amount": 30339.00, "batch_number": "25H3573VC4", "expiry_date": "2027-05-04"},
            {"product_id": p_sef400, "product_name": "Sefina 400Ml", "unit": "Bottle", "qty": 15.0, "unit_price": 1760.17, "amount": 26402.55, "batch_number": "DSE26001", "expiry_date": "2026-11-04"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SR/26-27/34", "2026-05-30", "Main Warehouse", "Direct", "Credit", "2026-05-30",
             "Scanned SLV Credit Note SR/26-27/34", json.dumps(items3), 56741.55, 0.0, 5106.74, 5106.74, 66955.00, 0.0, 66955.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 4. BILL #4: SLV/26-27/580 (30-05-2026) ----------------
    p_sta700 = await get_or_create_prod("Stamp Xtra 700Ml", "Pesticides", "Bottle", 854.00, 950.00, "DCS25021", "2027-03-12")
    p_del100 = await get_or_create_prod("Delegate 100Ml", "Pesticides", "Bottle", 1288.00, 1400.00, "26A2721D01", "2028-01-01")
    p_sum100 = await get_or_create_prod("Sumimax 100Ml", "Pesticides", "Bottle", 110.00, 130.00, "BSMX602003", "2028-02-13")
    p_meo500 = await get_or_create_prod("Meothrin 500Ml", "Pesticides", "Bottle", 760.00, 850.00, "VMTN603030", "2028-03-16")
    p_bor1 = await get_or_create_prod("Borolife 1Kg", "Fertilizers", "Packet", 310.00, 350.00, "BL1KG", "2028-05-30")
    p_eng160 = await get_or_create_prod("Engage 160Ml", "Pesticides", "Bottle", 1197.00, 1320.00, "24H2078MC0", "2026-08-22")
    p_gal1 = await get_or_create_prod("Galwan 1Lt", "Pesticides", "Bottle", 1150.00, 1260.00, "SIKRE49", "2027-08-05")

    inv4 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SLV/26-27/580", owner_id))
    if not inv4:
        await execute("UPDATE products SET current_stock = current_stock + 50 WHERE id = ?", (p_sta700,))
        await execute("UPDATE products SET current_stock = current_stock + 30 WHERE id = ?", (p_del100,))
        await execute("UPDATE products SET current_stock = current_stock + 120 WHERE id = ?", (p_sum100,))
        await execute("UPDATE products SET current_stock = current_stock + 25 WHERE id = ?", (p_eff280,))
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_meo500,))
        await execute("UPDATE products SET current_stock = current_stock + 10 WHERE id = ?", (p_bor1,))
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_eng160,))
        await execute("UPDATE products SET current_stock = current_stock + 50 WHERE id = ?", (p_gal1,))

        items4 = [
            {"product_id": p_sta700, "product_name": "Stamp Xtra 700Ml", "unit": "Bottle", "qty": 50.0, "unit_price": 723.73, "amount": 36186.50, "batch_number": "DCS25021", "expiry_date": "2027-03-12"},
            {"product_id": p_del100, "product_name": "Delegate 100Ml", "unit": "Bottle", "qty": 30.0, "unit_price": 1091.53, "amount": 32745.90, "batch_number": "26A2721D01", "expiry_date": "2028-01-01"},
            {"product_id": p_sum100, "product_name": "Sumimax 100Ml", "unit": "Bottle", "qty": 120.0, "unit_price": 93.22, "amount": 11186.40, "batch_number": "BSMX602003", "expiry_date": "2028-02-13"},
            {"product_id": p_eff280, "product_name": "Efficon 280Ml", "unit": "Bottle", "qty": 25.0, "unit_price": 1372.88, "amount": 34322.00, "batch_number": "ADZ224016", "expiry_date": "2026-07-27"},
            {"product_id": p_meo500, "product_name": "Meothrin 500Ml", "unit": "Bottle", "qty": 20.0, "unit_price": 644.07, "amount": 12881.40, "batch_number": "VMTN603030", "expiry_date": "2028-03-16"},
            {"product_id": p_bor1, "product_name": "Borolife 1Kg", "unit": "Packet", "qty": 10.0, "unit_price": 295.24, "amount": 2952.40, "batch_number": "BL1KG", "expiry_date": "2028-05-30"},
            {"product_id": p_eng160, "product_name": "Engage 160Ml", "unit": "Bottle", "qty": 20.0, "unit_price": 1014.41, "amount": 20288.20, "batch_number": "24H2078MC0", "expiry_date": "2026-08-22"},
            {"product_id": p_gal1, "product_name": "Galwan 1Lt", "unit": "Bottle", "qty": 50.0, "unit_price": 974.58, "amount": 48729.00, "batch_number": "SIKRE49", "expiry_date": "2027-08-05"},
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SLV/26-27/580", "2026-05-30", "Main Warehouse", "Direct", "Credit", "2026-05-30",
             "Scanned SLV Invoice SLV/26-27/580", json.dumps(items4), 199291.80, 0.0, 17744.37, 17744.37, 235084.00, 0.0, 235084.00, "Credit", "posted", owner_id, now_iso())
        )

    # ---------------- 5. BILL #5: SLV/26-27/1265 (09-07-2026) ----------------
    inv5 = await fetch_one("SELECT * FROM purchases WHERE invoice_number = ? AND owner_id = ?", ("SLV/26-27/1265", owner_id))
    if not inv5:
        await execute("UPDATE products SET current_stock = current_stock + 20 WHERE id = ?", (p_eng160,))
        items5 = [
            {"product_id": p_eng160, "product_name": "Engage 160Ml", "unit": "Bottle", "qty": 20.0, "unit_price": 1061.86, "amount": 21237.20, "batch_number": "25F2078GC0", "expiry_date": "2027-06-16"}
        ]
        await execute(
            """INSERT INTO purchases (id, supplier_id, supplier_name, invoice_number, invoice_date, warehouse, transporter, payment_terms, delivery_date, notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount, due_amount, payment_method, status, owner_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (uid(), sup_slv_id, "SRI LAKSHMI VENKATESWARA AGRO TRADERS", "SLV/26-27/1265", "2026-07-09", "Main Warehouse", "Direct", "Credit", "2026-07-09",
             "Scanned SLV Invoice SLV/26-27/1265", json.dumps(items5), 21237.20, 0.0, 1911.35, 1911.35, 25060.00, 0.0, 25060.00, "Credit", "posted", owner_id, now_iso())
        )

    print("Successfully added ALL 5 SLV Agro Traders invoices into ADMIN account!")

if __name__ == "__main__":
    asyncio.run(insert_5_slv_admin())
