"""AgriStock Pro - FastAPI backend (100% Offline SQLite + JWT). Per-user data isolation."""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import json
import logging
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_from_request,
)
from models import (
    LoginRequest, RegisterRequest, ProductIn, Product, CustomerIn, Customer, SupplierIn, Supplier,
    PurchaseIn, Purchase, SaleIn, Sale, Settings, now_iso, uid,
)
from database import init_db, execute, fetch_one, fetch_all

# In-memory store for brute-force login tracking
failed_attempts = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "admin123")
    name = os.environ.get("ADMIN_NAME", "Administrator")
    existing = await fetch_one("SELECT * FROM users WHERE username = ?", (username,))
    if not existing:
        await execute(
            "INSERT INTO users (id, username, name, role, password_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (uid(), username, name, "admin", hash_password(password), now_iso())
        )
    elif not verify_password(password, existing["password_hash"]):
        await execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (hash_password(password), username)
        )

    staff_password = os.environ.get("STAFF_PASSWORD", "user@123")
    for i in range(1, 11):
        uname = f"user{i}"
        if not await fetch_one("SELECT * FROM users WHERE username = ?", (uname,)):
            await execute(
                "INSERT INTO users (id, username, name, role, password_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (uid(), uname, "", "staff", hash_password(staff_password), now_iso())
            )
    yield


app = FastAPI(title="AgriStock Pro API (100% Offline SQLite)", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


def owner_q(user: dict):
    return user["id"]


async def current_user(req: Request) -> dict:
    user = await get_current_user_from_request(req)
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user


# ---------------- Auth ----------------
@api.post("/auth/register")
async def register_user(body: RegisterRequest):
    username = body.username.strip()
    if len(username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(body.password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")

    existing = await fetch_one("SELECT * FROM users WHERE username = ?", (username,))
    if existing:
        raise HTTPException(400, "Username already registered")

    user_id = uid()
    created = now_iso()
    pw_hash = hash_password(body.password)
    name = body.name.strip() if body.name else username

    await execute(
        "INSERT INTO users (id, username, name, role, password_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, username, name, "staff", pw_hash, created)
    )

    user_dict = {"id": user_id, "username": username, "name": name, "role": "staff", "created_at": created}
    token = create_access_token(user_id, username)
    resp = Response(content=json.dumps({"token": token, "user": user_dict}), media_type="application/json")
    resp.set_cookie("agri_token", token, httponly=True, samesite="lax", max_age=86400 * 7)
    resp.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=86400 * 7)
    return resp


@api.post("/auth/login")
async def login(body: LoginRequest, req: Request):
    uname = body.username.strip()
    now = datetime.now(timezone.utc)

    if uname in failed_attempts:
        attempts, lock_until = failed_attempts[uname]
        if lock_until and now < lock_until:
            wait_min = int((lock_until - now).total_seconds() / 60) + 1
            raise HTTPException(429, f"Account locked due to multiple failed logins. Try again in {wait_min} minutes.")
        elif lock_until and now >= lock_until:
            failed_attempts.pop(uname, None)

    user = await fetch_one("SELECT * FROM users WHERE username = ?", (uname,))
    if not user or not verify_password(body.password, user["password_hash"]):
        attempts, _ = failed_attempts.get(uname, (0, None))
        attempts += 1
        if attempts >= 5:
            lock_until = now + timedelta(minutes=15)
            failed_attempts[uname] = (attempts, lock_until)
            raise HTTPException(429, "Too many failed attempts. Account locked for 15 minutes.")
        else:
            failed_attempts[uname] = (attempts, None)
            raise HTTPException(401, f"Invalid username or password ({5 - attempts} attempts remaining)")

    failed_attempts.pop(uname, None)

    user_dict = {"id": user["id"], "username": user["username"], "name": user["name"], "role": user["role"], "created_at": user["created_at"]}
    token = create_access_token(user["id"], user["username"])
    resp = Response(content=json.dumps({"token": token, "user": user_dict}), media_type="application/json")
    resp.set_cookie("agri_token", token, httponly=True, samesite="lax", max_age=86400 * 7)
    resp.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=86400 * 7)
    return resp


@api.post("/auth/logout")
async def logout():
    resp = Response(content=json.dumps({"ok": True}), media_type="application/json")
    resp.delete_cookie("agri_token")
    resp.delete_cookie("access_token")
    return resp


@api.get("/auth/me")
async def me(user=Depends(current_user)):
    return user


# ---------------- Products ----------------
@api.get("/products")
async def list_products(
    q: str = "",
    category: str = "",
    company: str = "",
    stock: str = "",
    user=Depends(current_user),
):
    sql = "SELECT * FROM products WHERE owner_id = ?"
    params = [user["id"]]

    if q:
        sql += " AND (name LIKE ? OR company LIKE ? OR barcode LIKE ?)"
        like_q = f"%{q}%"
        params.extend([like_q, like_q, like_q])
    if category:
        sql += " AND category = ?"
        params.append(category)
    if company:
        sql += " AND company LIKE ?"
        params.append(f"%{company}%")
    if stock == "low":
        sql += " AND current_stock > 0 AND current_stock <= minimum_stock"
    elif stock == "out":
        sql += " AND current_stock <= 0"
    elif stock == "in":
        sql += " AND current_stock > 0"

    sql += " ORDER BY created_at DESC"
    return await fetch_all(sql, tuple(params))


@api.get("/products/{pid}")
async def get_product(pid: str, user=Depends(current_user)):
    p = await fetch_one("SELECT * FROM products WHERE id = ? AND owner_id = ?", (pid, user["id"]))
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@api.post("/products")
async def create_product(body: ProductIn, user=Depends(current_user)):
    p_data = body.model_dump()
    if p_data.get("opening_stock") is not None and not p_data.get("current_stock"):
        p_data["current_stock"] = p_data.pop("opening_stock")
    p = Product(**p_data)
    doc = p.model_dump()
    doc["owner_id"] = user["id"]

    await execute(
        """INSERT INTO products (
            id, owner_id, name, category, company, brand, barcode, batch_number,
            manufacture_date, expiry_date, unit, purchase_price, selling_price,
            current_stock, minimum_stock, rack_number, image_url, description, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            doc["id"], doc["owner_id"], doc["name"], doc["category"], doc["company"], doc["brand"],
            doc["barcode"], doc["batch_number"], doc["manufacture_date"], doc["expiry_date"],
            doc["unit"], doc["purchase_price"], doc["selling_price"], doc["current_stock"],
            doc["minimum_stock"], doc["rack_number"], doc["image_url"], doc["description"], doc["created_at"]
        )
    )
    return doc


@api.put("/products/{pid}")
async def update_product(pid: str, body: ProductIn, user=Depends(current_user)):
    existing = await fetch_one("SELECT * FROM products WHERE id = ? AND owner_id = ?", (pid, user["id"]))
    if not existing:
        raise HTTPException(404, "Product not found")

    data = body.model_dump()
    if data.get("opening_stock") is not None and not data.get("current_stock"):
        data["current_stock"] = data["opening_stock"]
    await execute(
        """UPDATE products SET
            name=?, category=?, company=?, brand=?, barcode=?, batch_number=?,
            manufacture_date=?, expiry_date=?, unit=?, purchase_price=?, selling_price=?,
            current_stock=?, minimum_stock=?, rack_number=?, image_url=?, description=?
        WHERE id=? AND owner_id=?""",
        (
            data["name"], data["category"], data["company"], data["brand"], data["barcode"],
            data["batch_number"], data["manufacture_date"], data["expiry_date"], data["unit"],
            data["purchase_price"], data["selling_price"], data["current_stock"], data["minimum_stock"],
            data["rack_number"], data["image_url"], data["description"], pid, user["id"]
        )
    )
    return await fetch_one("SELECT * FROM products WHERE id = ? AND owner_id = ?", (pid, user["id"]))


@api.delete("/products/{pid}")
async def delete_product(pid: str, user=Depends(current_user)):
    existing = await fetch_one("SELECT * FROM products WHERE id = ? AND owner_id = ?", (pid, user["id"]))
    if not existing:
        raise HTTPException(404, "Product not found")
    await execute("DELETE FROM products WHERE id = ? AND owner_id = ?", (pid, user["id"]))
    return {"ok": True}


# ---------------- Customers ----------------
@api.get("/customers")
async def list_customers(q: str = "", user=Depends(current_user)):
    sql = "SELECT * FROM customers WHERE owner_id = ?"
    params = [user["id"]]
    if q:
        sql += " AND (name LIKE ? OR phone LIKE ? OR area LIKE ?)"
        like_q = f"%{q}%"
        params.extend([like_q, like_q, like_q])
    sql += " ORDER BY created_at DESC"
    return await fetch_all(sql, tuple(params))


@api.post("/customers")
async def create_customer(body: CustomerIn, user=Depends(current_user)):
    c_data = body.model_dump()
    if c_data.get("opening_balance") and not c_data.get("current_due"):
        c_data["current_due"] = c_data["opening_balance"]
    c = Customer(**c_data)
    doc = c.model_dump()
    doc["owner_id"] = user["id"]

    await execute(
        """INSERT INTO customers (
            id, owner_id, name, phone, email, address, area, gst, credit_limit,
            opening_balance, current_due, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            doc["id"], doc["owner_id"], doc["name"], doc["phone"], doc["email"], doc["address"],
            doc["area"], doc["gst"], doc["credit_limit"], doc["opening_balance"],
            doc["current_due"], doc["status"], doc["created_at"]
        )
    )
    return doc


@api.put("/customers/{cid}")
async def update_customer(cid: str, body: CustomerIn, user=Depends(current_user)):
    existing = await fetch_one("SELECT * FROM customers WHERE id = ? AND owner_id = ?", (cid, user["id"]))
    if not existing:
        raise HTTPException(404, "Customer not found")

    data = body.model_dump()
    await execute(
        """UPDATE customers SET
            name=?, phone=?, email=?, address=?, area=?, gst=?, credit_limit=?,
            opening_balance=?, status=?
        WHERE id=? AND owner_id=?""",
        (
            data["name"], data["phone"], data["email"], data["address"], data["area"],
            data["gst"], data["credit_limit"], data["opening_balance"], data["status"],
            cid, user["id"]
        )
    )
    return await fetch_one("SELECT * FROM customers WHERE id = ? AND owner_id = ?", (cid, user["id"]))


@api.delete("/customers/{cid}")
async def delete_customer(cid: str, user=Depends(current_user)):
    existing = await fetch_one("SELECT * FROM customers WHERE id = ? AND owner_id = ?", (cid, user["id"]))
    if not existing:
        raise HTTPException(404, "Customer not found")
    await execute("DELETE FROM customers WHERE id = ? AND owner_id = ?", (cid, user["id"]))
    return {"ok": True}


# ---------------- Suppliers ----------------
@api.get("/suppliers")
async def list_suppliers(q: str = "", user=Depends(current_user)):
    sql = "SELECT * FROM suppliers WHERE owner_id = ?"
    params = [user["id"]]
    if q:
        sql += " AND (name LIKE ? OR company LIKE ? OR phone LIKE ?)"
        like_q = f"%{q}%"
        params.extend([like_q, like_q, like_q])
    sql += " ORDER BY created_at DESC"
    return await fetch_all(sql, tuple(params))


@api.post("/suppliers")
async def create_supplier(body: SupplierIn, user=Depends(current_user)):
    s_data = body.model_dump()
    if s_data.get("opening_balance") and not s_data.get("outstanding_amount"):
        s_data["outstanding_amount"] = s_data["opening_balance"]
    s = Supplier(**s_data)
    doc = s.model_dump()
    doc["owner_id"] = user["id"]

    await execute(
        """INSERT INTO suppliers (
            id, owner_id, name, company, phone, email, address, gst, bank_name,
            bank_account, ifsc, opening_balance, outstanding_amount, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            doc["id"], doc["owner_id"], doc["name"], doc["company"], doc["phone"], doc["email"],
            doc["address"], doc["gst"], doc["bank_name"], doc["bank_account"], doc["ifsc"],
            doc["opening_balance"], doc["outstanding_amount"], doc["status"], doc["created_at"]
        )
    )
    return doc


@api.put("/suppliers/{sid}")
async def update_supplier(sid: str, body: SupplierIn, user=Depends(current_user)):
    existing = await fetch_one("SELECT * FROM suppliers WHERE id = ? AND owner_id = ?", (sid, user["id"]))
    if not existing:
        raise HTTPException(404, "Supplier not found")

    data = body.model_dump()
    await execute(
        """UPDATE suppliers SET
            name=?, company=?, phone=?, email=?, address=?, gst=?, bank_name=?,
            bank_account=?, ifsc=?, opening_balance=?, status=?
        WHERE id=? AND owner_id=?""",
        (
            data["name"], data["company"], data["phone"], data["email"], data["address"],
            data["gst"], data["bank_name"], data["bank_account"], data["ifsc"],
            data["opening_balance"], data["status"], sid, user["id"]
        )
    )
    return await fetch_one("SELECT * FROM suppliers WHERE id = ? AND owner_id = ?", (sid, user["id"]))


@api.delete("/suppliers/{sid}")
async def delete_supplier(sid: str, user=Depends(current_user)):
    existing = await fetch_one("SELECT * FROM suppliers WHERE id = ? AND owner_id = ?", (sid, user["id"]))
    if not existing:
        raise HTTPException(404, "Supplier not found")
    await execute("DELETE FROM suppliers WHERE id = ? AND owner_id = ?", (sid, user["id"]))
    return {"ok": True}


# ---------------- Purchases ----------------
@api.get("/purchases")
async def list_purchases(q: str = "", user=Depends(current_user)):
    sql = "SELECT * FROM purchases WHERE owner_id = ?"
    params = [user["id"]]
    if q:
        sql += " AND (invoice_number LIKE ? OR supplier_name LIKE ?)"
        like_q = f"%{q}%"
        params.extend([like_q, like_q])
    sql += " ORDER BY created_at DESC"
    return await fetch_all(sql, tuple(params), json_fields=["items_json"])


@api.get("/purchases/{pid}")
async def get_purchase(pid: str, user=Depends(current_user)):
    doc = await fetch_one("SELECT * FROM purchases WHERE id = ? AND owner_id = ?", (pid, user["id"]), json_fields=["items_json"])
    if not doc:
        raise HTTPException(404, "Purchase not found")
    return doc


@api.post("/purchases")
async def create_purchase(body: PurchaseIn, user=Depends(current_user)):
    p = Purchase(**body.model_dump())
    doc = p.model_dump()
    doc["owner_id"] = user["id"]

    if p.supplier_name and not p.supplier_id:
        existing_s = await fetch_one("SELECT * FROM suppliers WHERE LOWER(name) = ? AND owner_id = ?", (p.supplier_name.strip().lower(), user["id"]))
        if existing_s:
            p.supplier_id = existing_s["id"]
            doc["supplier_id"] = existing_s["id"]
        else:
            new_s = Supplier(name=p.supplier_name.strip())
            s_doc = new_s.model_dump()
            s_doc["owner_id"] = user["id"]
            await execute(
                """INSERT INTO suppliers (
                    id, owner_id, name, company, phone, email, address, gst, bank_name,
                    bank_account, ifsc, opening_balance, outstanding_amount, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    s_doc["id"], s_doc["owner_id"], s_doc["name"], s_doc["company"], s_doc["phone"],
                    s_doc["email"], s_doc["address"], s_doc["gst"], s_doc["bank_name"], s_doc["bank_account"],
                    s_doc["ifsc"], s_doc["opening_balance"], s_doc["outstanding_amount"], s_doc["status"], s_doc["created_at"]
                )
            )
            p.supplier_id = new_s.id
            doc["supplier_id"] = new_s.id

    items_json_str = json.dumps(doc["items"])
    await execute(
        """INSERT INTO purchases (
            id, owner_id, supplier_id, supplier_name, invoice_number, invoice_date,
            warehouse, reference_number, transporter, payment_terms, delivery_date,
            notes, items_json, subtotal, discount, cgst, sgst, total, paid_amount,
            due_amount, payment_method, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            doc["id"], doc["owner_id"], doc["supplier_id"], doc["supplier_name"], doc["invoice_number"],
            doc["invoice_date"], doc["warehouse"], doc["reference_number"], doc["transporter"],
            doc["payment_terms"], doc["delivery_date"], doc["notes"], items_json_str,
            doc["subtotal"], doc["discount"], doc["cgst"], doc["sgst"], doc["total"],
            doc["paid_amount"], doc["due_amount"], doc["payment_method"], doc["status"], doc["created_at"]
        )
    )

    await execute(
        "INSERT INTO counters (owner_id, kind, seq) VALUES (?, 'purchase', 1) ON CONFLICT(owner_id, kind) DO UPDATE SET seq = seq + 1",
        (user["id"],)
    )

    if p.status == "posted":
        for it in p.items:
            await execute(
                """UPDATE products SET
                    current_stock = current_stock + ?,
                    batch_number = COALESCE(NULLIF(?, ''), batch_number),
                    expiry_date = COALESCE(NULLIF(?, ''), expiry_date),
                    manufacture_date = COALESCE(NULLIF(?, ''), manufacture_date)
                WHERE id = ? AND owner_id = ?""",
                (it.qty, it.batch_number or "", it.expiry_date or "", it.manufacture_date or "", it.product_id, user["id"])
            )
        if p.supplier_id:
            await execute(
                "UPDATE suppliers SET outstanding_amount = outstanding_amount + ? WHERE id = ? AND owner_id = ?",
                (p.due_amount, p.supplier_id, user["id"])
            )

    return await fetch_one("SELECT * FROM purchases WHERE id = ? AND owner_id = ?", (doc["id"], user["id"]), json_fields=["items_json"])


@api.put("/purchases/{pid}")
async def update_purchase(pid: str, body: PurchaseIn, user=Depends(current_user)):
    old_doc = await fetch_one("SELECT * FROM purchases WHERE id = ? AND owner_id = ?", (pid, user["id"]), json_fields=["items_json"])
    if not old_doc:
        raise HTTPException(404, "Purchase not found")

    if old_doc.get("status") == "posted":
        for it in old_doc.get("items", []):
            await execute(
                "UPDATE products SET current_stock = current_stock - ? WHERE id = ? AND owner_id = ?",
                (it.get("qty", 0), it.get("product_id"), user["id"])
            )
        if old_doc.get("supplier_id") and old_doc.get("due_amount", 0) > 0:
            await execute(
                "UPDATE suppliers SET outstanding_amount = outstanding_amount - ? WHERE id = ? AND owner_id = ?",
                (old_doc["due_amount"], old_doc["supplier_id"], user["id"])
            )

    data = body.model_dump()
    items_json_str = json.dumps(data["items"])
    await execute(
        """UPDATE purchases SET
            supplier_id=?, supplier_name=?, invoice_number=?, invoice_date=?, warehouse=?,
            reference_number=?, transporter=?, payment_terms=?, delivery_date=?, notes=?,
            items_json=?, subtotal=?, discount=?, cgst=?, sgst=?, total=?, paid_amount=?,
            due_amount=?, payment_method=?, status=?
        WHERE id=? AND owner_id=?""",
        (
            data["supplier_id"], data["supplier_name"], data["invoice_number"], data["invoice_date"],
            data["warehouse"], data["reference_number"], data["transporter"], data["payment_terms"],
            data["delivery_date"], data["notes"], items_json_str, data["subtotal"], data["discount"],
            data["cgst"], data["sgst"], data["total"], data["paid_amount"], data["due_amount"],
            data["payment_method"], data["status"], pid, user["id"]
        )
    )

    if body.status == "posted":
        for it in body.items:
            await execute(
                """UPDATE products SET
                    current_stock = current_stock + ?,
                    batch_number = COALESCE(NULLIF(?, ''), batch_number),
                    expiry_date = COALESCE(NULLIF(?, ''), expiry_date),
                    manufacture_date = COALESCE(NULLIF(?, ''), manufacture_date)
                WHERE id = ? AND owner_id = ?""",
                (it.qty, it.batch_number or "", it.expiry_date or "", it.manufacture_date or "", it.product_id, user["id"])
            )
        if body.supplier_id:
            await execute(
                "UPDATE suppliers SET outstanding_amount = outstanding_amount + ? WHERE id = ? AND owner_id = ?",
                (body.due_amount, body.supplier_id, user["id"])
            )

    return await fetch_one("SELECT * FROM purchases WHERE id = ? AND owner_id = ?", (pid, user["id"]), json_fields=["items_json"])


@api.delete("/purchases/{pid}")
async def delete_purchase(pid: str, user=Depends(current_user)):
    doc = await fetch_one("SELECT * FROM purchases WHERE id = ? AND owner_id = ?", (pid, user["id"]), json_fields=["items_json"])
    if not doc:
        raise HTTPException(404, "Purchase not found")

    if doc.get("status") == "posted":
        for it in doc.get("items", []):
            await execute(
                "UPDATE products SET current_stock = current_stock - ? WHERE id = ? AND owner_id = ?",
                (it.get("qty", 0), it.get("product_id"), user["id"])
            )
        if doc.get("supplier_id") and doc.get("due_amount", 0) > 0:
            await execute(
                "UPDATE suppliers SET outstanding_amount = outstanding_amount - ? WHERE id = ? AND owner_id = ?",
                (doc["due_amount"], doc["supplier_id"], user["id"])
            )

    await execute("DELETE FROM purchases WHERE id = ? AND owner_id = ?", (pid, user["id"]))
    return {"ok": True}


# ---------------- Sales ----------------
@api.get("/sales")
async def list_sales(q: str = "", user=Depends(current_user)):
    sql = "SELECT * FROM sales WHERE owner_id = ?"
    params = [user["id"]]
    if q:
        sql += " AND (invoice_number LIKE ? OR customer_name LIKE ?)"
        like_q = f"%{q}%"
        params.extend([like_q, like_q])
    sql += " ORDER BY created_at DESC"
    return await fetch_all(sql, tuple(params), json_fields=["items_json"])


@api.get("/sales/{sid}")
async def get_sale(sid: str, user=Depends(current_user)):
    doc = await fetch_one("SELECT * FROM sales WHERE id = ? AND owner_id = ?", (sid, user["id"]), json_fields=["items_json"])
    if not doc:
        raise HTTPException(404, "Sale not found")
    return doc


@api.post("/sales")
async def create_sale(body: SaleIn, user=Depends(current_user)):
    s = Sale(**body.model_dump())
    doc = s.model_dump()
    doc["owner_id"] = user["id"]

    if s.customer_name and not s.customer_id:
        existing_c = await fetch_one("SELECT * FROM customers WHERE LOWER(name) = ? AND owner_id = ?", (s.customer_name.strip().lower(), user["id"]))
        if existing_c:
            s.customer_id = existing_c["id"]
            doc["customer_id"] = existing_c["id"]
        else:
            new_c = Customer(name=s.customer_name.strip(), phone=s.customer_mobile or "", address=s.billing_address or "")
            c_doc = new_c.model_dump()
            c_doc["owner_id"] = user["id"]
            await execute(
                """INSERT INTO customers (
                    id, owner_id, name, phone, email, address, area, gst, credit_limit,
                    opening_balance, current_due, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    c_doc["id"], c_doc["owner_id"], c_doc["name"], c_doc["phone"], c_doc["email"],
                    c_doc["address"], c_doc["area"], c_doc["gst"], c_doc["credit_limit"],
                    c_doc["opening_balance"], c_doc["current_due"], c_doc["status"], c_doc["created_at"]
                )
            )
            s.customer_id = new_c.id
            doc["customer_id"] = new_c.id

    items_json_str = json.dumps(doc["items"])
    await execute(
        """INSERT INTO sales (
            id, owner_id, customer_id, customer_name, customer_mobile, billing_address,
            invoice_number, invoice_date, due_date, sales_person, sales_type, payment_terms,
            notes, items_json, subtotal, discount, cgst, sgst, total, received_amount,
            change_amount, payment_method, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            doc["id"], doc["owner_id"], doc["customer_id"], doc["customer_name"], doc["customer_mobile"],
            doc["billing_address"], doc["invoice_number"], doc["invoice_date"], doc["due_date"],
            doc["sales_person"], doc["sales_type"], doc["payment_terms"], doc["notes"], items_json_str,
            doc["subtotal"], doc["discount"], doc["cgst"], doc["sgst"], doc["total"],
            doc["received_amount"], doc["change_amount"], doc["payment_method"], doc["status"], doc["created_at"]
        )
    )

    await execute(
        "INSERT INTO counters (owner_id, kind, seq) VALUES (?, 'sale', 1) ON CONFLICT(owner_id, kind) DO UPDATE SET seq = seq + 1",
        (user["id"],)
    )

    if s.status == "posted":
        for it in s.items:
            await execute(
                "UPDATE products SET current_stock = current_stock - ? WHERE id = ? AND owner_id = ?",
                (it.qty, it.product_id, user["id"])
            )
        if s.customer_id:
            due = s.total - s.received_amount
            if due > 0:
                await execute(
                    "UPDATE customers SET current_due = current_due + ? WHERE id = ? AND owner_id = ?",
                    (due, s.customer_id, user["id"])
                )

    return await fetch_one("SELECT * FROM sales WHERE id = ? AND owner_id = ?", (doc["id"], user["id"]), json_fields=["items_json"])


@api.put("/sales/{sid}")
async def update_sale(sid: str, body: SaleIn, user=Depends(current_user)):
    old_doc = await fetch_one("SELECT * FROM sales WHERE id = ? AND owner_id = ?", (sid, user["id"]), json_fields=["items_json"])
    if not old_doc:
        raise HTTPException(404, "Sale not found")

    if old_doc.get("status") == "posted":
        for it in old_doc.get("items", []):
            await execute(
                "UPDATE products SET current_stock = current_stock + ? WHERE id = ? AND owner_id = ?",
                (it.get("qty", 0), it.get("product_id"), user["id"])
            )
        if old_doc.get("customer_id"):
            old_due = old_doc.get("total", 0) - old_doc.get("received_amount", 0)
            if old_due > 0:
                await execute(
                    "UPDATE customers SET current_due = current_due - ? WHERE id = ? AND owner_id = ?",
                    (old_due, old_doc["customer_id"], user["id"])
                )

    data = body.model_dump()
    items_json_str = json.dumps(data["items"])
    await execute(
        """UPDATE sales SET
            customer_id=?, customer_name=?, customer_mobile=?, billing_address=?, invoice_number=?,
            invoice_date=?, due_date=?, sales_person=?, sales_type=?, payment_terms=?, notes=?,
            items_json=?, subtotal=?, discount=?, cgst=?, sgst=?, total=?, received_amount=?,
            change_amount=?, payment_method=?, status=?
        WHERE id=? AND owner_id=?""",
        (
            data["customer_id"], data["customer_name"], data["customer_mobile"], data["billing_address"],
            data["invoice_number"], data["invoice_date"], data["due_date"], data["sales_person"],
            data["sales_type"], data["payment_terms"], data["notes"], items_json_str, data["subtotal"],
            data["discount"], data["cgst"], data["sgst"], data["total"], data["received_amount"],
            data["change_amount"], data["payment_method"], data["status"], sid, user["id"]
        )
    )

    if body.status == "posted":
        for it in body.items:
            await execute(
                "UPDATE products SET current_stock = current_stock - ? WHERE id = ? AND owner_id = ?",
                (it.qty, it.product_id, user["id"])
            )
        if body.customer_id:
            new_due = body.total - body.received_amount
            if new_due > 0:
                await execute(
                    "UPDATE customers SET current_due = current_due + ? WHERE id = ? AND owner_id = ?",
                    (new_due, body.customer_id, user["id"])
                )

    return await fetch_one("SELECT * FROM sales WHERE id = ? AND owner_id = ?", (sid, user["id"]), json_fields=["items_json"])


@api.delete("/sales/{sid}")
async def delete_sale(sid: str, user=Depends(current_user)):
    doc = await fetch_one("SELECT * FROM sales WHERE id = ? AND owner_id = ?", (sid, user["id"]), json_fields=["items_json"])
    if not doc:
        raise HTTPException(404, "Sale not found")

    if doc.get("status") == "posted":
        for it in doc.get("items", []):
            await execute(
                "UPDATE products SET current_stock = current_stock + ? WHERE id = ? AND owner_id = ?",
                (it.get("qty", 0), it.get("product_id"), user["id"])
            )
        if doc.get("customer_id"):
            due = doc.get("total", 0) - doc.get("received_amount", 0)
            if due > 0:
                await execute(
                    "UPDATE customers SET current_due = current_due - ? WHERE id = ? AND owner_id = ?",
                    (due, doc["customer_id"], user["id"])
                )

    await execute("DELETE FROM sales WHERE id = ? AND owner_id = ?", (sid, user["id"]))
    return {"ok": True}


# ---------------- Batches ----------------
@api.get("/batches")
async def list_batches(user=Depends(current_user)):
    sql = "SELECT id, id as product_id, name as product_name, batch_number, expiry_date, current_stock as stock, unit FROM products WHERE owner_id = ? AND batch_number != '' ORDER BY expiry_date ASC"
    return await fetch_all(sql, (user["id"],))


@api.get("/batches/expiring")
async def expiring_batches(days: int = 30, user=Depends(current_user)):
    cutoff = (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")
    sql = "SELECT id, id as product_id, name as product_name, batch_number, expiry_date, current_stock as stock, unit FROM products WHERE owner_id = ? AND batch_number != '' AND expiry_date != '' AND expiry_date <= ? ORDER BY expiry_date ASC"
    return await fetch_all(sql, (user["id"], cutoff))


# ---------------- Dashboard & Reports ----------------
@api.get("/dashboard/stats")
async def dashboard_stats(user=Depends(current_user)):
    uid = user["id"]
    sales_res = await fetch_one("SELECT COALESCE(SUM(total), 0) as total_sales, COUNT(*) as count FROM sales WHERE owner_id = ?", (uid,))
    pur_res = await fetch_one("SELECT COALESCE(SUM(total), 0) as total_purchases FROM purchases WHERE owner_id = ?", (uid,))
    cust_res = await fetch_one("SELECT COUNT(*) as total_customers, COALESCE(SUM(current_due), 0) as pending_dues FROM customers WHERE owner_id = ?", (uid,))
    prod_res = await fetch_one("SELECT COUNT(*) as total_products, COALESCE(SUM(CASE WHEN current_stock <= minimum_stock THEN 1 ELSE 0 END), 0) as low_stock_count FROM products WHERE owner_id = ?", (uid,))

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_sales_res = await fetch_one("SELECT COALESCE(SUM(total), 0) as today_sales FROM sales WHERE owner_id = ? AND invoice_date = ?", (uid, today_str))
    today_pur_res = await fetch_one("SELECT COALESCE(SUM(total), 0) as today_purchases FROM purchases WHERE owner_id = ? AND invoice_date = ?", (uid, today_str))

    recent_sales = await fetch_all("SELECT * FROM sales WHERE owner_id = ? ORDER BY created_at DESC LIMIT 5", (uid,), json_fields=["items_json"])
    recent_purchases = await fetch_all("SELECT * FROM purchases WHERE owner_id = ? ORDER BY created_at DESC LIMIT 5", (uid,), json_fields=["items_json"])
    low_stock = await fetch_all("SELECT * FROM products WHERE owner_id = ? AND current_stock <= minimum_stock LIMIT 5", (uid,))
    expiring_prod = await expiring_batches(days=30, user=user)

    trend = []
    for i in range(6, -1, -1):
        dt = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        day_res = await fetch_one("SELECT COALESCE(SUM(total), 0) as total FROM sales WHERE owner_id = ? AND invoice_date = ?", (uid, dt))
        trend.append({"date": dt, "total": round(day_res["total"], 2) if day_res else 0.0})

    return {
        "total_sales": round(sales_res["total_sales"], 2),
        "total_purchases": round(pur_res["total_purchases"], 2),
        "total_profit": round(sales_res["total_sales"] * 0.15, 2),
        "today_sales": round(today_sales_res["today_sales"], 2),
        "today_purchases": round(today_pur_res["today_purchases"], 2),
        "total_customers": cust_res["total_customers"],
        "pending_dues": round(cust_res["pending_dues"], 2),
        "total_products": prod_res["total_products"],
        "low_stock_count": prod_res["low_stock_count"],
        "recent_sales": recent_sales,
        "recent_purchases": recent_purchases,
        "low_stock_products": low_stock,
        "expiring_products": expiring_prod,
        "top_selling": [],
        "sales_trend": trend,
    }


@api.get("/reports/summary")
async def reports_summary(user=Depends(current_user)):
    uid = user["id"]
    sales_res = await fetch_one("SELECT COALESCE(SUM(total), 0) as total_sales, COALESCE(SUM(cgst), 0) as total_cgst, COALESCE(SUM(sgst), 0) as total_sgst, COUNT(*) as count FROM sales WHERE owner_id = ?", (uid,))
    pur_res = await fetch_one("SELECT COALESCE(SUM(total), 0) as total_purchases, COUNT(*) as count FROM purchases WHERE owner_id = ?", (uid,))

    monthly = []
    now = datetime.now(timezone.utc)
    for i in range(5, -1, -1):
        dt = now - timedelta(days=i * 30)
        ym = dt.strftime("%Y-%m")
        ms_res = await fetch_one("SELECT COALESCE(SUM(total), 0) as s FROM sales WHERE owner_id = ? AND invoice_date LIKE ?", (uid, f"{ym}%"))
        mp_res = await fetch_one("SELECT COALESCE(SUM(total), 0) as p FROM purchases WHERE owner_id = ? AND invoice_date LIKE ?", (uid, f"{ym}%"))
        monthly.append({
            "month": dt.strftime("%b %Y"),
            "sales": round(ms_res["s"], 2),
            "purchases": round(mp_res["p"], 2),
        })

    cat_res = await fetch_all("SELECT category, COUNT(*) as count, COALESCE(SUM(current_stock), 0) as stock FROM products WHERE owner_id = ? GROUP BY category", (uid,))
    top_cust = await fetch_all("SELECT customer_name as name, COALESCE(SUM(total), 0) as total FROM sales WHERE owner_id = ? AND customer_name != '' GROUP BY customer_name ORDER BY total DESC LIMIT 5", (uid,))
    top_sup = await fetch_all("SELECT supplier_name as name, COALESCE(SUM(total), 0) as total FROM purchases WHERE owner_id = ? AND supplier_name != '' GROUP BY supplier_name ORDER BY total DESC LIMIT 5", (uid,))

    return {
        "total_sales": round(sales_res["total_sales"], 2),
        "total_purchases": round(pur_res["total_purchases"], 2),
        "total_profit": round(sales_res["total_sales"] * 0.15, 2),
        "sales_count": sales_res["count"],
        "purchases_count": pur_res["count"],
        "monthly": monthly,
        "category_wise": cat_res,
        "tax": {
            "cgst": round(sales_res["total_cgst"], 2),
            "sgst": round(sales_res["total_sgst"], 2),
            "total": round(sales_res["total_cgst"] + sales_res["total_sgst"], 2),
        },
        "top_customers": top_cust,
        "top_suppliers": top_sup,
    }


# ---------------- Settings ----------------
@api.get("/settings")
async def get_settings(user=Depends(current_user)):
    s = await fetch_one("SELECT * FROM settings WHERE owner_id = ?", (user["id"],))
    if not s:
        defaults = Settings().model_dump()
        defaults["owner_id"] = user["id"]
        await execute(
            """INSERT INTO settings (
                owner_id, company_name, company_email, company_phone, company_address,
                gst_number, currency, currency_symbol, timezone, language,
                invoice_prefix_sale, invoice_prefix_purchase, logo_url, tax_rate,
                low_stock_alert, expiry_alert_days
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                defaults["owner_id"], defaults["company_name"], defaults["company_email"],
                defaults["company_phone"], defaults["company_address"], defaults["gst_number"],
                defaults["currency"], defaults["currency_symbol"], defaults["timezone"],
                defaults["language"], defaults["invoice_prefix_sale"], defaults["invoice_prefix_purchase"],
                defaults["logo_url"], defaults["tax_rate"], defaults["low_stock_alert"], defaults["expiry_alert_days"]
            )
        )
        return defaults
    return s


@api.put("/settings")
async def update_settings(body: Settings, user=Depends(current_user)):
    data = body.model_dump()
    data["owner_id"] = user["id"]
    await execute(
        """INSERT INTO settings (
            owner_id, company_name, company_email, company_phone, company_address,
            gst_number, currency, currency_symbol, timezone, language,
            invoice_prefix_sale, invoice_prefix_purchase, logo_url, tax_rate,
            low_stock_alert, expiry_alert_days
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(owner_id) DO UPDATE SET
            company_name=excluded.company_name, company_email=excluded.company_email,
            company_phone=excluded.company_phone, company_address=excluded.company_address,
            gst_number=excluded.gst_number, currency=excluded.currency,
            currency_symbol=excluded.currency_symbol, timezone=excluded.timezone,
            language=excluded.language, invoice_prefix_sale=excluded.invoice_prefix_sale,
            invoice_prefix_purchase=excluded.invoice_prefix_purchase,
            logo_url=excluded.logo_url, tax_rate=excluded.tax_rate,
            low_stock_alert=excluded.low_stock_alert, expiry_alert_days=excluded.expiry_alert_days""",
        (
            data["owner_id"], data["company_name"], data["company_email"], data["company_phone"],
            data["company_address"], data["gst_number"], data["currency"], data["currency_symbol"],
            data["timezone"], data["language"], data["invoice_prefix_sale"], data["invoice_prefix_purchase"],
            data["logo_url"], data["tax_rate"], data["low_stock_alert"], data["expiry_alert_days"]
        )
    )
    return await fetch_one("SELECT * FROM settings WHERE owner_id = ?", (user["id"],))


# ---------------- Meta ----------------
@api.get("/meta/next-invoice")
async def next_invoice(kind: str = "sale", user=Depends(current_user)):
    st = await get_settings(user)
    prefix = st.get("invoice_prefix_purchase" if kind == "purchase" else "invoice_prefix_sale", "INV-")

    count_res = await fetch_one(f"SELECT COUNT(*) as c FROM {'purchases' if kind == 'purchase' else 'sales'} WHERE owner_id = ?", (user["id"],))
    doc_count = count_res["c"] if count_res else 0

    counter_res = await fetch_one("SELECT seq FROM counters WHERE owner_id = ? AND kind = ?", (user["id"], kind))
    counter_seq = counter_res["seq"] if counter_res else 0

    next_seq = 10000 + max(doc_count, counter_seq) + 1
    return {"number": f"{prefix}{next_seq}"}


app.include_router(api)
