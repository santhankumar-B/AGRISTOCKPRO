import asyncio
import os
import sys
import uuid
import json
from datetime import datetime, timezone

sys.path.append(os.path.dirname(__file__))
from database import init_db, fetch_all, fetch_one, execute

def uid():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# Comprehensive Master Data Table with Exact Net Invoice Purchase Prices, Batch Numbers & Expiries
EXACT_PRODUCTS_DATA = [
    # 1. Gharda Chemicals Invoices (#4521601156)
    {
        "name": "Deltamethrin 11% W/W Ec (Boxerr-250 ML)",
        "category": "Pesticides",
        "unit": "Bottle",
        "purchase_price": 420.02, # Incl 18% GST (Taxable ₹355.95)
        "selling_price": 480.00,
        "batch_number": "BOX25E0125",
        "expiry_date": "2027-11-14",
        "company": "GHARDA CHEMICALS LIMITED"
    },
    {
        "name": "Deltamethrin 11% W/W Ec (Boxerr-500 ML)",
        "category": "Pesticides",
        "unit": "Bottle",
        "purchase_price": 831.55, # Incl 18% GST (Taxable ₹704.70)
        "selling_price": 920.00,
        "batch_number": "BOX26E0129",
        "expiry_date": "2028-04-10",
        "company": "GHARDA CHEMICALS LIMITED"
    },
    {
        "name": "Chlorpyrifos 50% + Cypermethrin 5% Ec (HAMLA 550-1 LTR)",
        "category": "Pesticides",
        "unit": "Bottle",
        "purchase_price": 686.05, # Incl 18% GST (Taxable ₹581.40)
        "selling_price": 760.00,
        "batch_number": "HML26E3342",
        "expiry_date": "2028-04-19",
        "company": "GHARDA CHEMICALS LIMITED"
    },
    {
        "name": "Chlorpyrifos 50% + Cypermethrin 5% Ec (HAMLA 550-500 ML)",
        "category": "Pesticides",
        "unit": "Bottle",
        "purchase_price": 351.52, # Incl 18% GST (Taxable ₹297.90)
        "selling_price": 400.00,
        "batch_number": "HML25E3264",
        "expiry_date": "2027-07-02",
        "company": "GHARDA CHEMICALS LIMITED"
    },
    {
        "name": "Chlorpyrifos 50% Ec (Ecoguard-1 LTR)",
        "category": "Pesticides",
        "unit": "Bottle",
        "purchase_price": 583.04, # Incl 18% GST (Taxable ₹494.10)
        "selling_price": 650.00,
        "batch_number": "ECO26E4586",
        "expiry_date": "2028-04-11",
        "company": "GHARDA CHEMICALS LIMITED"
    },
    {
        "name": "Indoxacarb 14.5% + Acetamiprid 7.7% W/W Sc (Kite-250 ML)",
        "category": "Pesticides",
        "unit": "Bottle",
        "purchase_price": 819.86, # Incl 18% GST (Taxable ₹694.80)
        "selling_price": 900.00,
        "batch_number": "KIT25J0113",
        "expiry_date": "2027-10-09",
        "company": "GHARDA CHEMICALS LIMITED"
    },
    {
        "name": "Profenofos 40% + Cypermethrin 4% Ec (Jugaad-1 LTR)",
        "category": "Pesticides",
        "unit": "Bottle",
        "purchase_price": 590.00, # Incl 18% GST (Taxable ₹500.00)
        "selling_price": 660.00,
        "batch_number": "PCM26E0206",
        "expiry_date": "2028-03-17",
        "company": "GHARDA CHEMICALS LIMITED"
    },

    # 2. T. Stanes Fertilizers & Micronutrients
    {
        "name": "ADDON (NPK-19-19-19) 25KG",
        "category": "Fertilizers",
        "unit": "Bag",
        "purchase_price": 3704.40, # Net per bag incl 5% tax
        "selling_price": 3900.00,
        "batch_number": "1919190925",
        "expiry_date": "2028-09-07",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "INFUSE (POTASSIUM SULPHATE) 25KG",
        "category": "Fertilizers",
        "unit": "Bag",
        "purchase_price": 2883.30, # Net per bag incl 5% tax
        "selling_price": 3100.00,
        "batch_number": "TS/SOP0725",
        "expiry_date": "2028-08-08",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "TAKEON (MONO POTASSIUM PHOSPHATE) 25KG",
        "category": "Fertilizers",
        "unit": "Bag",
        "purchase_price": 5153.40, # Net per bag incl 5% tax
        "selling_price": 5400.00,
        "batch_number": "S829684/25",
        "expiry_date": "2028-08-08",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "PROPLUS (CALCIUM NITRATE) 25KG",
        "category": "Fertilizers",
        "unit": "Bag",
        "purchase_price": 3064.00, # Net per bag incl 5% tax
        "selling_price": 3300.00,
        "batch_number": "TS/PN/0426",
        "expiry_date": "2030-04-29",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "HUGO (POTASSIUM NITRATE) 25KG",
        "category": "Fertilizers",
        "unit": "Bag",
        "purchase_price": 3438.75, # Net per bag incl 5% tax
        "selling_price": 3700.00,
        "batch_number": "TS/PN/0426",
        "expiry_date": "2030-04-29",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "STANES MICROFOOD LIQUID MICRONUTRIENTS 1 LT",
        "category": "Bio-Fertilizers",
        "unit": "Bottle",
        "purchase_price": 409.50, # Net per bottle incl 5% tax
        "selling_price": 460.00,
        "batch_number": "102",
        "expiry_date": "2027-06-21",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "STANES MICROFOOD SPECIAL FOLIAR SPRAY ALL CROP FOLIAR 500 GM",
        "category": "Bio-Fertilizers",
        "unit": "Packet",
        "purchase_price": 126.79, # Net per packet incl 5% tax
        "selling_price": 150.00,
        "batch_number": "MFF1025234",
        "expiry_date": "2028-10-27",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "STANES MICROFOOD SPECIAL FOLIAR SPRAY ALL CROP FOLIAR 1 KG",
        "category": "Bio-Fertilizers",
        "unit": "Packet",
        "purchase_price": 247.28, # Net per packet incl 5% tax
        "selling_price": 280.00,
        "batch_number": "MFF0226308",
        "expiry_date": "2029-02-27",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "STANES MICROFOOD LIQUID MICRONUTRIENTS 500 ML",
        "category": "Bio-Fertilizers",
        "unit": "Bottle",
        "purchase_price": 217.88, # Net per bottle incl 5% tax
        "selling_price": 250.00,
        "batch_number": "LMF1225195",
        "expiry_date": "2027-11-29",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "STANES MICROFOOD LIQUID MICRONUTRIENTS 5 LT",
        "category": "Bio-Fertilizers",
        "unit": "Can",
        "purchase_price": 1752.45, # Net per 5L Can incl 5% tax
        "selling_price": 1950.00,
        "batch_number": "114",
        "expiry_date": "2027-07-03",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "STANES MICROFOOD LIQUID MICRONUTRIENTS 20 LT",
        "category": "Bio-Fertilizers",
        "unit": "Can",
        "purchase_price": 6955.20, # Net per 20L Can incl 5% tax
        "selling_price": 7500.00,
        "batch_number": "LMF052646V21",
        "expiry_date": "2028-04-27",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "WEKTOCON 1LT",
        "category": "Bio-Pesticides",
        "unit": "Bottle",
        "purchase_price": 1811.30, # Net per bottle incl 18% tax
        "selling_price": 2000.00,
        "batch_number": "WK022635",
        "expiry_date": "2028-01-21",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "WEKTOCON 500ML",
        "category": "Bio-Pesticides",
        "unit": "Bottle",
        "purchase_price": 917.33, # Net per bottle incl 18% tax
        "selling_price": 1050.00,
        "batch_number": "WK122532",
        "expiry_date": "2027-11-19",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "LIQUID BIONEMATON (Paecilomyces Lilacinus) 1 LT",
        "category": "Bio-Pesticides",
        "unit": "Bottle",
        "purchase_price": 328.51, # Net per bottle incl 18% tax
        "selling_price": 380.00,
        "batch_number": "BN392",
        "expiry_date": "2027-01-22",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "STANOWET 250ML",
        "category": "Bio-Pesticides",
        "unit": "Bottle",
        "purchase_price": 150.57, # Net per bottle incl 18% tax
        "selling_price": 180.00,
        "batch_number": "ST072515",
        "expiry_date": "2027-07-14",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "NIMBECIDINE 10000 PPM (TS) 250ML",
        "category": "Bio-Pesticides",
        "unit": "Bottle",
        "purchase_price": 540.79, # Net per bottle incl 18% tax
        "selling_price": 620.00,
        "batch_number": "S12510005",
        "expiry_date": "2027-09-29",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "NIMBECIDINE 300 PPM (TS) 1LT",
        "category": "Bio-Pesticides",
        "unit": "Bottle",
        "purchase_price": 492.77, # Net per bottle incl 18% tax
        "selling_price": 560.00,
        "batch_number": "S0-032602018",
        "expiry_date": "2028-02-16",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "NIMBECIDINE 300 PPM (TS) 500ML",
        "category": "Bio-Pesticides",
        "unit": "Bottle",
        "purchase_price": 250.75, # Net per bottle incl 18% tax
        "selling_price": 290.00,
        "batch_number": "S0-032602018",
        "expiry_date": "2028-02-16",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "STANES GREEN MIRACLE (STRESS ALLEVIATOR) 1 LT",
        "category": "Bio-Pesticides",
        "unit": "Bottle",
        "purchase_price": 497.49, # Net per bottle incl 18% tax
        "selling_price": 560.00,
        "batch_number": "GM0526112",
        "expiry_date": "2028-04-28",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "STANES GREEN MIRACLE (STRESS ALLEVIATOR) 500 ML",
        "category": "Bio-Pesticides",
        "unit": "Bottle",
        "purchase_price": 253.11, # Net per bottle incl 18% tax
        "selling_price": 290.00,
        "batch_number": "GM0526104",
        "expiry_date": "2027-04-27",
        "company": "T. STANES AND COMPANY LIMITED"
    },
    {
        "name": "STANES GREEN MIRACLE (STRESS ALLEVIATOR) 5 LT",
        "category": "Bio-Pesticides",
        "unit": "Can",
        "purchase_price": 2441.07, # Net per 5L Can incl 18% tax
        "selling_price": 2750.00,
        "batch_number": "GM0526106",
        "expiry_date": "2028-04-28",
        "company": "T. STANES AND COMPANY LIMITED"
    }
]

async def fix_exact_prices_and_batches():
    init_db()
    users = await fetch_all("SELECT * FROM users")
    if not users:
        print("No users found.")
        return

    for u in users:
        owner_id = u["id"]
        username = u["username"]
        print(f"Updating exact invoice prices & batch numbers for user: {username}...")

        # 1. Update/Insert exact product prices, batch numbers, expiries
        for item in EXACT_PRODUCTS_DATA:
            p = await fetch_one("SELECT * FROM products WHERE name = ? AND owner_id = ?", (item["name"], owner_id))
            if p:
                await execute(
                    """UPDATE products 
                       SET purchase_price = ?, selling_price = ?, batch_number = ?, expiry_date = ?, unit = ?
                       WHERE id = ?""",
                    (item["purchase_price"], item["selling_price"], item["batch_number"], item["expiry_date"], item["unit"], p["id"])
                )
            else:
                await execute(
                    """INSERT INTO products (id, name, category, company, brand, barcode, current_stock, minimum_stock, unit, purchase_price, selling_price, batch_number, expiry_date, owner_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (uid(), item["name"], item["category"], item["company"], "Brand",
                     f"89030310{int(uuid.uuid4().int) % 100000:05d}", 10.0, 2.0, item["unit"], item["purchase_price"], item["selling_price"], item["batch_number"], item["expiry_date"], owner_id, now_iso())
                )

        # 2. Update line item prices inside purchases table to match exact per-unit net costs
        purchases = await fetch_all("SELECT * FROM purchases WHERE owner_id = ?", (owner_id,))
        for pur in purchases:
            items = json.loads(pur["items_json"]) if pur["items_json"] else []
            updated = False
            for line in items:
                p_name = line.get("product_name")
                matching = next((x for x in EXACT_PRODUCTS_DATA if x["name"] == p_name), None)
                if matching:
                    line["unit_price"] = matching["purchase_price"]
                    line["batch_number"] = matching["batch_number"]
                    line["expiry_date"] = matching["expiry_date"]
                    line["unit"] = matching["unit"]
                    line["amount"] = round(line["qty"] * matching["purchase_price"], 2)
                    updated = True
            if updated:
                await execute(
                    "UPDATE purchases SET items_json = ? WHERE id = ?",
                    (json.dumps(items), pur["id"])
                )

    print("Exact invoice prices, batch numbers & expiries successfully fixed across all accounts!")

if __name__ == "__main__":
    asyncio.run(fix_exact_prices_and_batches())
