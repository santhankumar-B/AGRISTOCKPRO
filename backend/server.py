"""AgriStock Pro - FastAPI backend (MongoDB + JWT). Per-user data isolation."""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import logging
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from contextlib import asynccontextmanager
from pymongo import ReturnDocument
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

try:
    import certifi
    ca_file = certifi.where()
except ImportError:
    ca_file = None

mongo_url = os.environ["MONGO_URL"]
client_kwargs = {"tlsAllowInvalidCertificates": True}
if ca_file:
    client_kwargs["tlsCAFile"] = ca_file

client = AsyncIOMotorClient(mongo_url, **client_kwargs)
db = client[os.environ["DB_NAME"]]

# In-memory store for brute-force login tracking
failed_attempts = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.users.create_index("username", unique=True)
    await db.products.create_index([("owner_id", 1), ("name", 1)])
    await db.products.create_index([("owner_id", 1), ("barcode", 1)])
    await db.customers.create_index([("owner_id", 1), ("name", 1)])
    await db.suppliers.create_index([("owner_id", 1), ("name", 1)])
    await db.sales.create_index([("owner_id", 1), ("invoice_number", 1)])
    await db.purchases.create_index([("owner_id", 1), ("invoice_number", 1)])
    await db.settings.create_index("owner_id", unique=True, sparse=True)

    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "admin123")
    name = os.environ.get("ADMIN_NAME", "Administrator")
    existing = await db.users.find_one({"username": username})
    if not existing:
        await db.users.insert_one({
            "id": uid(), "username": username, "name": name, "role": "admin",
            "password_hash": hash_password(password), "created_at": now_iso(),
        })
    elif not verify_password(password, existing["password_hash"]):
        await db.users.update_one({"username": username},
                                  {"$set": {"password_hash": hash_password(password)}})

    staff_password = os.environ.get("STAFF_PASSWORD", "user@123")
    for i in range(1, 11):
        uname = f"user{i}"
        if not await db.users.find_one({"username": uname}):
            await db.users.insert_one({
                "id": uid(), "username": uname, "name": "", "role": "staff",
                "password_hash": hash_password(staff_password), "created_at": now_iso(),
            })
    yield
    # Shutdown
    client.close()


app = FastAPI(title="AgriStock Pro API", lifespan=lifespan)
api = APIRouter(prefix="/api")


async def current_user(request: Request):
    return await get_current_user_from_request(request, db)


def owner_q(user):
    """Mandatory ownership filter — every scoped query MUST include this."""
    return {"owner_id": user["id"]}


# ---------------- Auth ----------------
@api.post("/auth/login")
async def login(body: LoginRequest, response: Response):
    uname_clean = body.username.strip().lower()
    now = datetime.now(timezone.utc)

    # Check brute-force lockout
    record = failed_attempts.get(uname_clean)
    if record and record.get("lockout_until"):
        if now < record["lockout_until"]:
            raise HTTPException(status_code=429, detail="Too many failed login attempts. Account temporarily locked for 15 minutes.")
        else:
            failed_attempts.pop(uname_clean, None)

    user = await db.users.find_one({"username": body.username.strip()}) or await db.users.find_one({"username": uname_clean})
    if not user or not verify_password(body.password, user["password_hash"]):
        rec = failed_attempts.setdefault(uname_clean, {"count": 0, "lockout_until": None})
        rec["count"] += 1
        if rec["count"] >= 5:
            rec["lockout_until"] = now + timedelta(minutes=15)
            raise HTTPException(status_code=429, detail="Too many failed login attempts. Account temporarily locked for 15 minutes.")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Successful login -> reset failed attempts
    failed_attempts.pop(uname_clean, None)

    token = create_access_token(user["id"], user["username"])
    response.set_cookie(key="access_token", value=token, httponly=True, secure=False,
                        samesite="lax", max_age=60 * 60 * 12, path="/")
    return {"token": token, "user": {"id": user["id"], "username": user["username"],
            "name": user["name"], "role": user.get("role", "staff"), "created_at": user.get("created_at", now_iso())}}


@api.post("/auth/register")
async def register(body: RegisterRequest, response: Response):
    uname = body.username.strip()
    if not uname or not body.password or not body.name.strip():
        raise HTTPException(status_code=400, detail="Username, password, and name are required")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    existing = await db.users.find_one({"username": uname}) or await db.users.find_one({"username": uname.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Username is already registered")

    user_id = uid()
    user_doc = {
        "id": user_id,
        "username": uname,
        "name": body.name.strip(),
        "role": "admin",
        "password_hash": hash_password(body.password),
        "created_at": now_iso(),
    }
    await db.users.insert_one(user_doc)
    token = create_access_token(user_id, uname)
    response.set_cookie(key="access_token", value=token, httponly=True, secure=False,
                        samesite="lax", max_age=60 * 60 * 12, path="/")
    return {
        "token": token,
        "user": {
            "id": user_id,
            "username": uname,
            "name": body.name.strip(),
            "role": "admin",
            "created_at": user_doc["created_at"],
        }
    }


@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@api.get("/auth/me")
async def me(user=Depends(current_user)):
    return user


class _ProfileIn(BaseModel):
    name: str


@api.put("/auth/profile")
async def update_profile(body: _ProfileIn, user=Depends(current_user)):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    await db.users.update_one({"id": user["id"]}, {"$set": {"name": name}})
    doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})
    return doc


# ---------------- Products ----------------
@api.get("/products")
async def list_products(q: str = "", category: str = "", company: str = "", stock: str = "", user=Depends(current_user)):
    query = dict(owner_q(user))
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"barcode": {"$regex": q, "$options": "i"}},
            {"batch_number": {"$regex": q, "$options": "i"}},
        ]
    if category:
        query["category"] = category
    if company:
        query["company"] = company
    docs = await db.products.find(query, {"_id": 0}).sort("created_at", -1).to_list(2000)
    if stock == "low":
        docs = [d for d in docs if 0 < d.get("current_stock", 0) <= d.get("minimum_stock", 0)]
    elif stock == "out":
        docs = [d for d in docs if d.get("current_stock", 0) <= 0]
    elif stock == "in":
        docs = [d for d in docs if d.get("current_stock", 0) > d.get("minimum_stock", 0)]
    return docs


@api.post("/products")
async def create_product(body: ProductIn, user=Depends(current_user)):
    p = Product(**body.model_dump(), current_stock=body.opening_stock)
    doc = p.model_dump()
    doc["owner_id"] = user["id"]  # server-stamped, not from client
    await db.products.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api.get("/products/{pid}")
async def get_product(pid: str, user=Depends(current_user)):
    doc = await db.products.find_one({"id": pid, **owner_q(user)}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Product not found")
    return doc


@api.put("/products/{pid}")
async def update_product(pid: str, body: ProductIn, user=Depends(current_user)):
    res = await db.products.update_one({"id": pid, **owner_q(user)}, {"$set": body.model_dump()})
    if res.matched_count == 0:
        raise HTTPException(404, "Product not found")
    return await db.products.find_one({"id": pid, **owner_q(user)}, {"_id": 0})


@api.delete("/products/{pid}")
async def delete_product(pid: str, user=Depends(current_user)):
    res = await db.products.delete_one({"id": pid, **owner_q(user)})
    if res.deleted_count == 0:
        raise HTTPException(404, "Product not found")
    return {"ok": True}


# ---------------- Customers ----------------
@api.get("/customers")
async def list_customers(q: str = "", user=Depends(current_user)):
    query = dict(owner_q(user))
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"phone": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
        ]
    return await db.customers.find(query, {"_id": 0}).sort("created_at", -1).to_list(2000)


@api.post("/customers")
async def create_customer(body: CustomerIn, user=Depends(current_user)):
    c = Customer(**body.model_dump(), current_due=body.opening_balance)
    doc = c.model_dump()
    doc["owner_id"] = user["id"]
    await db.customers.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api.put("/customers/{cid}")
async def update_customer(cid: str, body: CustomerIn, user=Depends(current_user)):
    res = await db.customers.update_one({"id": cid, **owner_q(user)}, {"$set": body.model_dump()})
    if res.matched_count == 0:
        raise HTTPException(404, "Customer not found")
    return await db.customers.find_one({"id": cid, **owner_q(user)}, {"_id": 0})


@api.delete("/customers/{cid}")
async def delete_customer(cid: str, user=Depends(current_user)):
    res = await db.customers.delete_one({"id": cid, **owner_q(user)})
    if res.deleted_count == 0:
        raise HTTPException(404, "Customer not found")
    return {"ok": True}


# ---------------- Suppliers ----------------
@api.get("/suppliers")
async def list_suppliers(q: str = "", user=Depends(current_user)):
    query = dict(owner_q(user))
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"company": {"$regex": q, "$options": "i"}},
            {"phone": {"$regex": q, "$options": "i"}},
        ]
    return await db.suppliers.find(query, {"_id": 0}).sort("created_at", -1).to_list(2000)


@api.post("/suppliers")
async def create_supplier(body: SupplierIn, user=Depends(current_user)):
    s = Supplier(**body.model_dump(), outstanding_amount=body.opening_balance)
    doc = s.model_dump()
    doc["owner_id"] = user["id"]
    await db.suppliers.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api.put("/suppliers/{sid}")
async def update_supplier(sid: str, body: SupplierIn, user=Depends(current_user)):
    res = await db.suppliers.update_one({"id": sid, **owner_q(user)}, {"$set": body.model_dump()})
    if res.matched_count == 0:
        raise HTTPException(404, "Supplier not found")
    return await db.suppliers.find_one({"id": sid, **owner_q(user)}, {"_id": 0})


@api.delete("/suppliers/{sid}")
async def delete_supplier(sid: str, user=Depends(current_user)):
    res = await db.suppliers.delete_one({"id": sid, **owner_q(user)})
    if res.deleted_count == 0:
        raise HTTPException(404, "Supplier not found")
    return {"ok": True}


# ---------------- Purchases ----------------
@api.get("/purchases")
async def list_purchases(q: str = "", user=Depends(current_user)):
    query = dict(owner_q(user))
    if q:
        query["$or"] = [
            {"invoice_number": {"$regex": q, "$options": "i"}},
            {"supplier_name": {"$regex": q, "$options": "i"}},
        ]
    return await db.purchases.find(query, {"_id": 0}).sort("created_at", -1).to_list(2000)


@api.post("/purchases")
async def create_purchase(body: PurchaseIn, user=Depends(current_user)):
    p = Purchase(**body.model_dump())
    doc = p.model_dump()
    doc["owner_id"] = user["id"]

    if p.supplier_name and not p.supplier_id:
        existing_s = await db.suppliers.find_one({"name": {"$regex": f"^{p.supplier_name.strip()}$", "$options": "i"}, **owner_q(user)})
        if existing_s:
            p.supplier_id = existing_s["id"]
            doc["supplier_id"] = existing_s["id"]
        else:
            new_s = Supplier(name=p.supplier_name.strip())
            s_doc = new_s.model_dump()
            s_doc["owner_id"] = user["id"]
            await db.suppliers.insert_one(s_doc)
            p.supplier_id = new_s.id
            doc["supplier_id"] = new_s.id

    await db.purchases.insert_one(doc)
    await db.counters.update_one(
        {"owner_id": user["id"], "kind": "purchase"},
        {"$inc": {"seq": 1}},
        upsert=True,
    )
    if p.status == "posted":
        for it in p.items:
            # Only mutate stock on products owned by this user
            await db.products.update_one(
                {"id": it.product_id, **owner_q(user)},
                {"$inc": {"current_stock": it.qty}, "$set": {
                    "batch_number": it.batch_number or "",
                    "expiry_date": it.expiry_date or "",
                    "manufacture_date": it.manufacture_date or "",
                }},
            )
        if p.supplier_id:
            await db.suppliers.update_one(
                {"id": p.supplier_id, **owner_q(user)},
                {"$inc": {"outstanding_amount": p.due_amount}},
            )
    doc.pop("_id", None)
    return doc


@api.get("/purchases/{pid}")
async def get_purchase(pid: str, user=Depends(current_user)):
    doc = await db.purchases.find_one({"id": pid, **owner_q(user)}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Purchase not found")
    return doc


@api.put("/purchases/{pid}")
async def update_purchase(pid: str, body: PurchaseIn, user=Depends(current_user)):
    old_doc = await db.purchases.find_one({"id": pid, **owner_q(user)})
    if not old_doc:
        raise HTTPException(404, "Purchase not found")

    if old_doc.get("status") == "posted":
        for it in old_doc.get("items", []):
            await db.products.update_one(
                {"id": it.get("product_id"), **owner_q(user)},
                {"$inc": {"current_stock": -it.get("qty", 0)}},
            )
        if old_doc.get("supplier_id") and old_doc.get("due_amount", 0) > 0:
            await db.suppliers.update_one(
                {"id": old_doc["supplier_id"], **owner_q(user)},
                {"$inc": {"outstanding_amount": -old_doc["due_amount"]}},
            )

    new_data = body.model_dump()
    new_data["owner_id"] = user["id"]
    await db.purchases.update_one({"id": pid, **owner_q(user)}, {"$set": new_data})

    if body.status == "posted":
        for it in body.items:
            await db.products.update_one(
                {"id": it.product_id, **owner_q(user)},
                {"$inc": {"current_stock": it.qty}, "$set": {
                    "batch_number": it.batch_number or "",
                    "expiry_date": it.expiry_date or "",
                    "manufacture_date": it.manufacture_date or "",
                }},
            )
        if body.supplier_id:
            await db.suppliers.update_one(
                {"id": body.supplier_id, **owner_q(user)},
                {"$inc": {"outstanding_amount": body.due_amount}},
            )

    return await db.purchases.find_one({"id": pid, **owner_q(user)}, {"_id": 0})


@api.delete("/purchases/{pid}")
async def delete_purchase(pid: str, user=Depends(current_user)):
    doc = await db.purchases.find_one({"id": pid, **owner_q(user)})
    if not doc:
        raise HTTPException(404, "Purchase not found")
    if doc.get("status") == "posted":
        for it in doc.get("items", []):
            await db.products.update_one(
                {"id": it["product_id"], **owner_q(user)},
                {"$inc": {"current_stock": -it.get("qty", 0)}},
            )
        if doc.get("supplier_id") and doc.get("due_amount", 0) > 0:
            await db.suppliers.update_one(
                {"id": doc["supplier_id"], **owner_q(user)},
                {"$inc": {"outstanding_amount": -doc["due_amount"]}},
            )
    await db.purchases.delete_one({"id": pid, **owner_q(user)})
    return {"ok": True}


# ---------------- Sales ----------------
@api.get("/sales")
async def list_sales(q: str = "", user=Depends(current_user)):
    query = dict(owner_q(user))
    if q:
        query["$or"] = [
            {"invoice_number": {"$regex": q, "$options": "i"}},
            {"customer_name": {"$regex": q, "$options": "i"}},
        ]
    return await db.sales.find(query, {"_id": 0}).sort("created_at", -1).to_list(2000)


@api.post("/sales")
async def create_sale(body: SaleIn, user=Depends(current_user)):
    s = Sale(**body.model_dump())
    doc = s.model_dump()
    doc["owner_id"] = user["id"]

    if s.customer_name and not s.customer_id:
        existing_c = await db.customers.find_one({"name": {"$regex": f"^{s.customer_name.strip()}$", "$options": "i"}, **owner_q(user)})
        if existing_c:
            s.customer_id = existing_c["id"]
            doc["customer_id"] = existing_c["id"]
        else:
            new_c = Customer(name=s.customer_name.strip(), phone=s.customer_mobile or "", address=s.billing_address or "")
            c_doc = new_c.model_dump()
            c_doc["owner_id"] = user["id"]
            await db.customers.insert_one(c_doc)
            s.customer_id = new_c.id
            doc["customer_id"] = new_c.id

    await db.sales.insert_one(doc)
    await db.counters.update_one(
        {"owner_id": user["id"], "kind": "sale"},
        {"$inc": {"seq": 1}},
        upsert=True,
    )
    if s.status == "posted":
        for it in s.items:
            await db.products.update_one(
                {"id": it.product_id, **owner_q(user)},
                {"$inc": {"current_stock": -it.qty}},
            )
        if s.customer_id:
            due = s.total - s.received_amount
            if due > 0:
                await db.customers.update_one(
                    {"id": s.customer_id, **owner_q(user)},
                    {"$inc": {"current_due": due}},
                )
    doc.pop("_id", None)
    return doc


@api.get("/sales/{sid}")
async def get_sale(sid: str, user=Depends(current_user)):
    doc = await db.sales.find_one({"id": sid, **owner_q(user)}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Sale not found")
    return doc


@api.put("/sales/{sid}")
async def update_sale(sid: str, body: SaleIn, user=Depends(current_user)):
    old_doc = await db.sales.find_one({"id": sid, **owner_q(user)})
    if not old_doc:
        raise HTTPException(404, "Sale not found")

    if old_doc.get("status") == "posted":
        for it in old_doc.get("items", []):
            await db.products.update_one(
                {"id": it.get("product_id"), **owner_q(user)},
                {"$inc": {"current_stock": it.get("qty", 0)}},
            )
        if old_doc.get("customer_id"):
            old_due = old_doc.get("total", 0) - old_doc.get("received_amount", 0)
            if old_due > 0:
                await db.customers.update_one(
                    {"id": old_doc["customer_id"], **owner_q(user)},
                    {"$inc": {"current_due": -old_due}},
                )

    new_data = body.model_dump()
    new_data["owner_id"] = user["id"]
    await db.sales.update_one({"id": sid, **owner_q(user)}, {"$set": new_data})

    if body.status == "posted":
        for it in body.items:
            await db.products.update_one(
                {"id": it.product_id, **owner_q(user)},
                {"$inc": {"current_stock": -it.qty}},
            )
        if body.customer_id:
            new_due = body.total - body.received_amount
            if new_due > 0:
                await db.customers.update_one(
                    {"id": body.customer_id, **owner_q(user)},
                    {"$inc": {"current_due": new_due}},
                )

    return await db.sales.find_one({"id": sid, **owner_q(user)}, {"_id": 0})


@api.delete("/sales/{sid}")
async def delete_sale(sid: str, user=Depends(current_user)):
    doc = await db.sales.find_one({"id": sid, **owner_q(user)})
    if not doc:
        raise HTTPException(404, "Sale not found")
    if doc.get("status") == "posted":
        for it in doc.get("items", []):
            await db.products.update_one(
                {"id": it["product_id"], **owner_q(user)},
                {"$inc": {"current_stock": it.get("qty", 0)}},
            )
        if doc.get("customer_id"):
            due = doc.get("total", 0) - doc.get("received_amount", 0)
            if due > 0:
                await db.customers.update_one(
                    {"id": doc["customer_id"], **owner_q(user)},
                    {"$inc": {"current_due": -due}},
                )
    await db.sales.delete_one({"id": sid, **owner_q(user)})
    return {"ok": True}


# ---------------- Batches ----------------
@api.get("/batches")
async def list_batches(user=Depends(current_user)):
    query = {**owner_q(user), "$or": [{"batch_number": {"$ne": ""}}, {"expiry_date": {"$ne": ""}}]}
    return await db.products.find(query, {"_id": 0}).sort("expiry_date", 1).to_list(2000)


@api.get("/batches/expiring")
async def expiring_batches(days: int = 90, user=Depends(current_user)):
    threshold = (datetime.now(timezone.utc) + timedelta(days=days)).date().isoformat()
    query = {**owner_q(user), "expiry_date": {"$ne": "", "$lte": threshold}}
    return await db.products.find(query, {"_id": 0}).sort("expiry_date", 1).to_list(2000)


# ---------------- Dashboard ----------------
@api.get("/dashboard/stats")
async def dashboard_stats(user=Depends(current_user)):
    today = datetime.now(timezone.utc).date().isoformat()
    q = owner_q(user)
    products = await db.products.find(q, {"_id": 0}).to_list(5000)
    total_products = len(products)
    low_stock = [p for p in products if 0 < p.get("current_stock", 0) <= p.get("minimum_stock", 0)]
    out_of_stock = [p for p in products if p.get("current_stock", 0) <= 0]
    expired = [p for p in products if p.get("expiry_date") and p["expiry_date"] < today]
    exp_threshold = (datetime.now(timezone.utc) + timedelta(days=90)).date().isoformat()
    expiring = [p for p in products if p.get("expiry_date") and today <= p["expiry_date"] <= exp_threshold]

    sales_today = await db.sales.find({**q, "invoice_date": today}, {"_id": 0}).to_list(1000)
    purchases_today = await db.purchases.find({**q, "invoice_date": today}, {"_id": 0}).to_list(1000)
    all_sales = await db.sales.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
    all_purchases = await db.purchases.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)

    trend = []
    for i in range(6, -1, -1):
        d = (datetime.now(timezone.utc) - timedelta(days=i)).date().isoformat()
        day_total = sum(s.get("total", 0) for s in all_sales if s.get("invoice_date") == d)
        trend.append({"date": d, "total": round(day_total, 2)})

    counter = {}
    for s in all_sales:
        for it in s.get("items", []):
            key = it["product_id"]
            counter.setdefault(key, {"product_id": key, "product_name": it.get("product_name", ""),
                                     "qty": 0, "amount": 0, "unit": it.get("unit", "")})
            counter[key]["qty"] += it.get("qty", 0)
            counter[key]["amount"] += it.get("amount", 0)
    top_selling = sorted(counter.values(), key=lambda x: x["qty"], reverse=True)[:5]
    prod_map = {p["id"]: p for p in products}
    for t in top_selling:
        p = prod_map.get(t["product_id"], {})
        t["image_url"] = p.get("image_url", "")
        t["category"] = p.get("category", "")

    return {
        "total_products": total_products,
        "today_sales": round(sum(s.get("total", 0) for s in sales_today), 2),
        "today_purchases": round(sum(p.get("total", 0) for p in purchases_today), 2),
        "low_stock_count": len(low_stock),
        "out_of_stock_count": len(out_of_stock),
        "expired_count": len(expired),
        "expiring_count": len(expiring),
        "recent_sales": all_sales[:5],
        "recent_purchases": all_purchases[:5],
        "low_stock_products": low_stock[:5],
        "expiring_products": expiring[:5],
        "sales_trend": trend,
        "top_selling": top_selling,
    }


# ---------------- Reports ----------------
def _top_by(rows, name_field, amount_field):
    agg = {}
    for r in rows:
        n = r.get(name_field) or "Walk-in"
        agg.setdefault(n, {"name": n, "amount": 0, "count": 0})
        agg[n]["amount"] += r.get(amount_field, 0)
        agg[n]["count"] += 1
    return sorted(agg.values(), key=lambda x: x["amount"], reverse=True)


@api.get("/reports/summary")
async def reports_summary(user=Depends(current_user)):
    q = owner_q(user)
    sales = await db.sales.find(q, {"_id": 0}).to_list(5000)
    purchases = await db.purchases.find(q, {"_id": 0}).to_list(5000)
    total_sales = sum(s.get("total", 0) for s in sales)
    total_purchases = sum(p.get("total", 0) for p in purchases)
    profit = total_sales - total_purchases

    months = []
    for i in range(5, -1, -1):
        d = datetime.now(timezone.utc) - timedelta(days=30 * i)
        m = d.strftime("%Y-%m")
        s_total = sum(s.get("total", 0) for s in sales if s.get("invoice_date", "").startswith(m))
        p_total = sum(p.get("total", 0) for p in purchases if p.get("invoice_date", "").startswith(m))
        months.append({"month": d.strftime("%b"), "sales": round(s_total, 2),
                       "purchases": round(p_total, 2), "profit": round(s_total - p_total, 2)})

    products = await db.products.find(q, {"_id": 0}).to_list(5000)
    cat_map = {}
    for p in products:
        c = p.get("category") or "Uncategorized"
        cat_map.setdefault(c, {"category": c, "products": 0, "stock_value": 0})
        cat_map[c]["products"] += 1
        cat_map[c]["stock_value"] += p.get("current_stock", 0) * p.get("purchase_price", 0)
    category_wise = list(cat_map.values())

    tax = {"cgst": sum(s.get("cgst", 0) for s in sales), "sgst": sum(s.get("sgst", 0) for s in sales)}

    return {
        "total_sales": round(total_sales, 2),
        "total_purchases": round(total_purchases, 2),
        "total_profit": round(profit, 2),
        "sales_count": len(sales),
        "purchase_count": len(purchases),
        "monthly": months,
        "category_wise": category_wise,
        "tax": tax,
        "top_customers": _top_by(sales, "customer_name", "total")[:5],
        "top_suppliers": _top_by(purchases, "supplier_name", "total")[:5],
    }


# ---------------- Settings (per-user) ----------------
@api.get("/settings")
async def get_settings(user=Depends(current_user)):
    doc = await db.settings.find_one(owner_q(user), {"_id": 0})
    if not doc:
        s = Settings().model_dump()
        s["owner_id"] = user["id"]
        await db.settings.insert_one(s)
        s.pop("_id", None)
        s.pop("owner_id", None)
        return s
    doc.pop("owner_id", None)
    return doc


@api.put("/settings")
async def update_settings(body: Settings, user=Depends(current_user)):
    data = body.model_dump()
    data["owner_id"] = user["id"]
    await db.settings.update_one(owner_q(user), {"$set": data}, upsert=True)
    data.pop("owner_id", None)
    return data


# ---------------- Meta ----------------
@api.get("/meta/next-invoice")
async def next_invoice(kind: str = "sale", user=Depends(current_user)):
    settings = await db.settings.find_one(owner_q(user), {"_id": 0}) or {}
    if kind == "sale":
        prefix = settings.get("invoice_prefix_sale", "INV-")
        doc_count = await db.sales.count_documents(owner_q(user))
    else:
        prefix = settings.get("invoice_prefix_purchase", "PUR-")
        doc_count = await db.purchases.count_documents(owner_q(user))

    ctr = await db.counters.find_one({"owner_id": user["id"], "kind": kind})
    counter_seq = ctr.get("seq", 0) if ctr else 0
    next_num = max(doc_count, counter_seq) + 1
    return {"number": f"{prefix}{10000 + next_num}"}


@api.get("/")
async def root():
    return {"app": "AgriStock Pro", "status": "ok"}


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
