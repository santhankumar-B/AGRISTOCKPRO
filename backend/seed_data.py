import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.append(os.path.dirname(__file__))
from database import init_db, fetch_one, fetch_all, execute

def uid():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

async def seed_data():
    init_db()
    
    # Get all users
    users = await fetch_all("SELECT * FROM users")
    if not users:
        print("No users found. Please start the backend server first to seed default users.")
        return

    for user in users:
        owner_id = user["id"]
        username = user["username"]
        print(f"Seeding rich sample data for user: {username} (ID: {owner_id})...")

        # 1. Products
        products_data = [
            {
                "name": "Urea Fertilizer 45kg",
                "category": "Fertilizers",
                "company": "IFFCO Ltd",
                "brand": "IFFCO",
                "barcode": "890123456001",
                "batch_number": "UF-2026-01",
                "manufacture_date": "2026-01-10",
                "expiry_date": "2028-01-10",
                "unit": "Bag",
                "purchase_price": 242.0,
                "selling_price": 268.0,
                "current_stock": 150.0,
                "minimum_stock": 20.0,
                "rack_number": "A-01",
                "description": "High nitrogen fertilizer for rapid plant growth."
            },
            {
                "name": "DAP Fertilizer 50kg",
                "category": "Fertilizers",
                "company": "Coromandel International",
                "brand": "Gromor",
                "barcode": "890123456002",
                "batch_number": "DAP-2026-04",
                "manufacture_date": "2026-02-01",
                "expiry_date": "2028-02-01",
                "unit": "Bag",
                "purchase_price": 1250.0,
                "selling_price": 1350.0,
                "current_stock": 80.0,
                "minimum_stock": 15.0,
                "rack_number": "A-02",
                "description": "Di-Ammonium Phosphate for root development and strength."
            },
            {
                "name": "Glyphosate 41% SL 1L",
                "category": "Pesticides",
                "company": "Syngenta India",
                "brand": "Touchdown",
                "barcode": "890123456003",
                "batch_number": "GLY-2026-02",
                "manufacture_date": "2026-01-15",
                "expiry_date": "2027-12-31",
                "unit": "Bottle",
                "purchase_price": 420.0,
                "selling_price": 480.0,
                "current_stock": 45.0,
                "minimum_stock": 10.0,
                "rack_number": "B-05",
                "description": "Non-selective systemic herbicide for weed management."
            },
            {
                "name": "Chlorpyrifos 20% EC 500ml",
                "category": "Pesticides",
                "company": "Tata Rallis",
                "brand": "Tafaban",
                "barcode": "890123456004",
                "batch_number": "CHP-2026-03",
                "manufacture_date": "2026-02-10",
                "expiry_date": "2027-08-30",
                "unit": "Bottle",
                "purchase_price": 280.0,
                "selling_price": 330.0,
                "current_stock": 60.0,
                "minimum_stock": 12.0,
                "rack_number": "B-06",
                "description": "Broad-spectrum insecticide for soil and foliar pests."
            },
            {
                "name": "Hybrid Paddy Seed RNR 15048 10kg",
                "category": "Seeds",
                "company": "Nuziveedu Seeds",
                "brand": "Telangana Sona",
                "barcode": "890123456005",
                "batch_number": "PADDY-26",
                "manufacture_date": "2026-03-01",
                "expiry_date": "2026-11-15",
                "unit": "Bag",
                "purchase_price": 650.0,
                "selling_price": 750.0,
                "current_stock": 40.0,
                "minimum_stock": 10.0,
                "rack_number": "C-01",
                "description": "Low GI high-yielding rice variety seeds."
            },
            {
                "name": "Cotton Hybrid Seeds BG-II 475g",
                "category": "Seeds",
                "company": "Bayer CropScience",
                "brand": "Bollgard II",
                "barcode": "890123456006",
                "batch_number": "COT-BG2",
                "manufacture_date": "2026-02-20",
                "expiry_date": "2026-09-30",
                "unit": "Packet",
                "purchase_price": 780.0,
                "selling_price": 860.0,
                "current_stock": 30.0,
                "minimum_stock": 5.0,
                "rack_number": "C-02",
                "description": "Bollworm resistant high-yield cotton seed."
            },
            {
                "name": "Bio-NPK Granules 10kg",
                "category": "Bio-Fertilizers",
                "company": "AgriBio Tech",
                "brand": "BioGro",
                "barcode": "890123456007",
                "batch_number": "BIO-01",
                "manufacture_date": "2026-01-05",
                "expiry_date": "2027-05-20",
                "unit": "Bag",
                "purchase_price": 320.0,
                "selling_price": 400.0,
                "current_stock": 50.0,
                "minimum_stock": 8.0,
                "rack_number": "D-03",
                "description": "Organic bio-fertilizer enriched with beneficial microbes."
            }
        ]

        prod_id_map = {}
        for p in products_data:
            existing_p = await fetch_one("SELECT * FROM products WHERE name = ? AND owner_id = ?", (p["name"], owner_id))
            if not existing_p:
                pid = uid()
                await execute(
                    """INSERT INTO products (
                        id, owner_id, name, category, company, brand, barcode, batch_number,
                        manufacture_date, expiry_date, unit, purchase_price, selling_price,
                        current_stock, minimum_stock, rack_number, image_url, description, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        pid, owner_id, p["name"], p["category"], p["company"], p["brand"],
                        p["barcode"], p["batch_number"], p["manufacture_date"], p["expiry_date"],
                        p["unit"], p["purchase_price"], p["selling_price"], p["current_stock"],
                        p["minimum_stock"], p["rack_number"], "", p["description"], now_iso()
                    )
                )
                prod_id_map[p["name"]] = pid
            else:
                prod_id_map[p["name"]] = existing_p["id"]

        # 2. Customers
        customers_data = [
            {
                "name": "Ramesh Kumar",
                "phone": "9876543210",
                "email": "ramesh@farm.in",
                "address": "Main Road, Village Farm",
                "area": "North Block",
                "gst": "36AAAPK1234A1Z9",
                "credit_limit": 50000.0,
                "opening_balance": 0.0,
                "current_due": 4500.0,
                "status": "active"
            },
            {
                "name": "Suresh Patel",
                "phone": "9812345678",
                "email": "suresh@greenvalley.in",
                "address": "Plot 14, Green Valley",
                "area": "South District",
                "gst": "",
                "credit_limit": 30000.0,
                "opening_balance": 0.0,
                "current_due": 1200.0,
                "status": "active"
            },
            {
                "name": "Venkatesh Rao",
                "phone": "9944556677",
                "email": "venkat@agrihub.com",
                "address": "Canal Road, Agri Hub",
                "area": "East Zone",
                "gst": "",
                "credit_limit": 40000.0,
                "opening_balance": 0.0,
                "current_due": 0.0,
                "status": "active"
            }
        ]

        cust_id_map = {}
        for c in customers_data:
            existing_c = await fetch_one("SELECT * FROM customers WHERE name = ? AND owner_id = ?", (c["name"], owner_id))
            if not existing_c:
                cid = uid()
                await execute(
                    """INSERT INTO customers (
                        id, owner_id, name, phone, email, address, area, gst, credit_limit,
                        opening_balance, current_due, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        cid, owner_id, c["name"], c["phone"], c["email"], c["address"],
                        c["area"], c["gst"], c["credit_limit"], c["opening_balance"],
                        c["current_due"], c["status"], now_iso()
                    )
                )
                cust_id_map[c["name"]] = cid
            else:
                cust_id_map[c["name"]] = existing_c["id"]

        # 3. Suppliers
        suppliers_data = [
            {
                "name": "IFFCO Fertilizer Corp",
                "company": "IFFCO Ltd",
                "phone": "040-23456789",
                "email": "sales@iffco.in",
                "address": "Fertilizer Complex, Sector 4",
                "gst": "36AAAAA1234A1Z1",
                "bank_name": "State Bank of India",
                "bank_account": "30123456789",
                "ifsc": "SBIN0001234",
                "opening_balance": 0.0,
                "outstanding_amount": 15000.0,
                "status": "active"
            },
            {
                "name": "Coromandel International",
                "company": "Coromandel Ltd",
                "phone": "040-87654321",
                "email": "orders@coromandel.biz",
                "address": "Coromandel House, MG Road",
                "gst": "36BBBBB5678B1Z2",
                "bank_name": "HDFC Bank",
                "bank_account": "50100234567",
                "ifsc": "HDFC0000456",
                "opening_balance": 0.0,
                "outstanding_amount": 8000.0,
                "status": "active"
            },
            {
                "name": "Syngenta India Ltd",
                "company": "Syngenta",
                "phone": "020-99887766",
                "email": "support@syngenta.com",
                "address": "Agri Tech Park, Phase II",
                "gst": "36CCCCC9012C1Z3",
                "bank_name": "ICICI Bank",
                "bank_account": "00040501234",
                "ifsc": "ICIC0000004",
                "opening_balance": 0.0,
                "outstanding_amount": 0.0,
                "status": "active"
            }
        ]

        sup_id_map = {}
        for s in suppliers_data:
            existing_s = await fetch_one("SELECT * FROM suppliers WHERE name = ? AND owner_id = ?", (s["name"], owner_id))
            if not existing_s:
                sid = uid()
                await execute(
                    """INSERT INTO suppliers (
                        id, owner_id, name, company, phone, email, address, gst, bank_name,
                        bank_account, ifsc, opening_balance, outstanding_amount, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        sid, owner_id, s["name"], s["company"], s["phone"], s["email"],
                        s["address"], s["gst"], s["bank_name"], s["bank_account"], s["ifsc"],
                        s["opening_balance"], s["outstanding_amount"], s["status"], now_iso()
                    )
                )
                sup_id_map[s["name"]] = sid
            else:
                sup_id_map[s["name"]] = existing_s["id"]

        # 4. Purchases
        purchases_count = await fetch_one("SELECT COUNT(*) as cnt FROM purchases WHERE owner_id = ?", (owner_id,))
        if purchases_count["cnt"] == 0:
            import json
            pur1_items = [
                {
                    "product_id": prod_id_map.get("Urea Fertilizer 45kg"),
                    "product_name": "Urea Fertilizer 45kg",
                    "unit": "Bag",
                    "qty": 100,
                    "unit_price": 242.0,
                    "amount": 24200.0
                }
            ]
            pur2_items = [
                {
                    "product_id": prod_id_map.get("DAP Fertilizer 50kg"),
                    "product_name": "DAP Fertilizer 50kg",
                    "unit": "Bag",
                    "qty": 50,
                    "unit_price": 1250.0,
                    "amount": 62500.0
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
                    uid(), owner_id, sup_id_map.get("IFFCO Fertilizer Corp", ""), "IFFCO Fertilizer Corp",
                    "PUR-2026-001", "2026-07-01", "Main Warehouse", "REF-101", "VRL Logistics",
                    "Net 30", "2026-07-02", "Bulk urea order for kharif season", json.dumps(pur1_items),
                    24200.0, 0.0, 0.0, 0.0, 24200.0, 9200.0, 15000.0, "Bank Transfer", "posted", now_iso()
                )
            )
            await execute(
                """INSERT INTO purchases (
                    id, owner_id, supplier_id, supplier_name, invoice_number, invoice_date,
                    warehouse, reference_number, transporter, payment_terms, delivery_date,
                    notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount,
                    due_amount, payment_method, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    uid(), owner_id, sup_id_map.get("Coromandel International", ""), "Coromandel International",
                    "PUR-2026-002", "2026-07-05", "Main Warehouse", "REF-102", "Gati KWE",
                    "Net 15", "2026-07-06", "DAP stock order", json.dumps(pur2_items),
                    62500.0, 0.0, 0.0, 0.0, 62500.0, 54500.0, 8000.0, "UPI", "posted", now_iso()
                )
            )

        # 5. Sales
        sales_count = await fetch_one("SELECT COUNT(*) as cnt FROM sales WHERE owner_id = ?", (owner_id,))
        if sales_count["cnt"] == 0:
            import json
            sal1_items = [
                {
                    "product_id": prod_id_map.get("Urea Fertilizer 45kg"),
                    "product_name": "Urea Fertilizer 45kg",
                    "unit": "Bag",
                    "qty": 10,
                    "unit_price": 268.0,
                    "amount": 2680.0
                }
            ]
            sal2_items = [
                {
                    "product_id": prod_id_map.get("DAP Fertilizer 50kg"),
                    "product_name": "DAP Fertilizer 50kg",
                    "unit": "Bag",
                    "qty": 2,
                    "unit_price": 1350.0,
                    "amount": 2700.0
                }
            ]
            await execute(
                """INSERT INTO sales (
                    id, owner_id, customer_id, customer_name, customer_mobile, billing_address,
                    invoice_number, invoice_date, due_date, sales_person, sales_type, payment_terms,
                    notes, items_json, subtotal, discount, cgst, sgst, total, received_amount,
                    change_amount, payment_method, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    uid(), owner_id, cust_id_map.get("Ramesh Kumar", ""), "Ramesh Kumar", "9876543210",
                    "Main Road, Village Farm", "INV-2026-001", "2026-07-10", "2026-07-25", "Store Admin",
                    "Direct Sale", "Credit", "Fertilizer purchase for paddy field", json.dumps(sal1_items),
                    2680.0, 0.0, 0.0, 0.0, 2680.0, 0.0, 0.0, "Credit", "posted", now_iso()
                )
            )
            await execute(
                """INSERT INTO sales (
                    id, owner_id, customer_id, customer_name, customer_mobile, billing_address,
                    invoice_number, invoice_date, due_date, sales_person, sales_type, payment_terms,
                    notes, items_json, subtotal, discount, cgst, sgst, total, received_amount,
                    change_amount, payment_method, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    uid(), owner_id, cust_id_map.get("Suresh Patel", ""), "Suresh Patel", "9812345678",
                    "Plot 14, Green Valley", "INV-2026-002", "2026-07-12", "2026-07-20", "Store Admin",
                    "Direct Sale", "Partial", "DAP purchase", json.dumps(sal2_items),
                    2700.0, 0.0, 0.0, 0.0, 2700.0, 1500.0, 0.0, "Cash", "posted", now_iso()
                )
            )

        print(f"Sample data successfully populated for user {username}!")

if __name__ == "__main__":
    asyncio.run(seed_data())
