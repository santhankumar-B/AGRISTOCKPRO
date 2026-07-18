"""Full backend API tests for AgriStock Pro.

Covers: auth, products, customers, suppliers, purchases, sales, batches,
dashboard, reports, settings, meta, and end-to-end stock flow.
"""
import os
import time
import requests
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / "frontend" / ".env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")


# ---------------- Auth ----------------
class TestAuth:
    def test_login_success(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/login",
                            json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 20
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"
        # cookie set
        assert "access_token" in r.cookies

    def test_login_wrong_password(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/login",
                            json={"username": "admin", "password": "wrongpass"})
        assert r.status_code == 401

    def test_login_missing_user(self, api_client):
        r = api_client.post(f"{BASE_URL}/api/auth/login",
                            json={"username": "no_such_user_xyz", "password": "x"})
        assert r.status_code == 401

    def test_me_with_bearer(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        assert r.json()["username"] == "admin"
        assert "password_hash" not in r.json()

    def test_me_without_token(self, api_client):
        r = requests.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401

    def test_logout(self, api_client):
        # login into fresh session so we get cookie
        s = requests.Session()
        login = s.post(f"{BASE_URL}/api/auth/login",
                       json={"username": "admin", "password": "admin123"})
        assert login.status_code == 200
        r = s.post(f"{BASE_URL}/api/auth/logout")
        assert r.status_code == 200
        assert r.json().get("ok") is True

    def test_register_and_login(self, api_client):
        uname = f"testreg_{int(time.time())}"
        r = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "username": uname, "password": "regpassword123", "name": "Registered User"
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert "token" in data
        assert data["user"]["username"] == uname

        # Verify login works with new user
        r_login = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "username": uname, "password": "regpassword123"
        })
        assert r_login.status_code == 200

    def test_lockout_after_failed_attempts(self, api_client):
        lock_user = f"lockuser_{int(time.time())}"
        # create user first
        api_client.post(f"{BASE_URL}/api/auth/register", json={
            "username": lock_user, "password": "correctpassword", "name": "Lockout Test"
        })

        # 5 failed login attempts
        for _ in range(5):
            r = api_client.post(f"{BASE_URL}/api/auth/login", json={
                "username": lock_user, "password": "wrongpassword"
            })
            assert r.status_code in (401, 429)

        # 6th attempt should return 429
        r_locked = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "username": lock_user, "password": "correctpassword"
        })
        assert r_locked.status_code == 429


# ---------------- Products ----------------
class TestProducts:
    def test_create_get_update_delete(self, auth_client):
        payload = {
            "name": "TEST_Urea_50kg",
            "category": "Fertilizer",
            "company": "TEST_Co",
            "unit": "Bag",
            "purchase_price": 100.0,
            "selling_price": 120.0,
            "opening_stock": 50,
            "minimum_stock": 10,
            "batch_number": "B-TEST-1",
            "expiry_date": "2099-01-01",
        }
        # CREATE
        r = auth_client.post(f"{BASE_URL}/api/products", json=payload)
        assert r.status_code == 200, r.text
        p = r.json()
        assert p["name"] == payload["name"]
        assert p["current_stock"] == 50  # set from opening_stock
        assert "id" in p
        pid = p["id"]

        # GET single
        r = auth_client.get(f"{BASE_URL}/api/products/{pid}")
        assert r.status_code == 200
        assert r.json()["id"] == pid

        # LIST
        r = auth_client.get(f"{BASE_URL}/api/products")
        assert r.status_code == 200
        assert any(x["id"] == pid for x in r.json())

        # UPDATE
        upd = dict(payload)
        upd["selling_price"] = 150.0
        r = auth_client.put(f"{BASE_URL}/api/products/{pid}", json=upd)
        assert r.status_code == 200
        assert r.json()["selling_price"] == 150.0

        # verify persisted
        r = auth_client.get(f"{BASE_URL}/api/products/{pid}")
        assert r.json()["selling_price"] == 150.0

        # DELETE
        r = auth_client.delete(f"{BASE_URL}/api/products/{pid}")
        assert r.status_code == 200

        r = auth_client.get(f"{BASE_URL}/api/products/{pid}")
        assert r.status_code == 404

    def test_product_filters(self, auth_client):
        # Create 3 products with varying stock levels
        created_ids = []
        try:
            p1 = auth_client.post(f"{BASE_URL}/api/products", json={
                "name": "TEST_FILTER_A", "category": "Seed",
                "opening_stock": 100, "minimum_stock": 10,
            }).json()
            created_ids.append(p1["id"])
            p2 = auth_client.post(f"{BASE_URL}/api/products", json={
                "name": "TEST_FILTER_B", "category": "Pesticide",
                "opening_stock": 5, "minimum_stock": 10,  # low
            }).json()
            created_ids.append(p2["id"])
            p3 = auth_client.post(f"{BASE_URL}/api/products", json={
                "name": "TEST_FILTER_C", "category": "Seed",
                "opening_stock": 0, "minimum_stock": 5,  # out
            }).json()
            created_ids.append(p3["id"])

            # q filter
            r = auth_client.get(f"{BASE_URL}/api/products?q=TEST_FILTER_A")
            assert r.status_code == 200
            names = [x["name"] for x in r.json()]
            assert "TEST_FILTER_A" in names

            # category filter
            r = auth_client.get(f"{BASE_URL}/api/products?category=Seed")
            names = [x["name"] for x in r.json()]
            assert "TEST_FILTER_A" in names and "TEST_FILTER_C" in names

            # stock=low
            r = auth_client.get(f"{BASE_URL}/api/products?stock=low")
            names = [x["name"] for x in r.json()]
            assert "TEST_FILTER_B" in names
            assert "TEST_FILTER_A" not in names

            # stock=out
            r = auth_client.get(f"{BASE_URL}/api/products?stock=out")
            names = [x["name"] for x in r.json()]
            assert "TEST_FILTER_C" in names

            # stock=in
            r = auth_client.get(f"{BASE_URL}/api/products?stock=in")
            names = [x["name"] for x in r.json()]
            assert "TEST_FILTER_A" in names
        finally:
            for i in created_ids:
                auth_client.delete(f"{BASE_URL}/api/products/{i}")


# ---------------- Customers ----------------
class TestCustomers:
    def test_customer_crud(self, auth_client):
        payload = {"name": "TEST_Customer_1", "phone": "9999900001",
                   "email": "test1@example.com", "opening_balance": 500}
        r = auth_client.post(f"{BASE_URL}/api/customers", json=payload)
        assert r.status_code == 200
        c = r.json()
        assert c["current_due"] == 500
        cid = c["id"]

        r = auth_client.get(f"{BASE_URL}/api/customers")
        assert any(x["id"] == cid for x in r.json())

        upd = dict(payload)
        upd["phone"] = "9999900002"
        r = auth_client.put(f"{BASE_URL}/api/customers/{cid}", json=upd)
        assert r.status_code == 200
        assert r.json()["phone"] == "9999900002"

        r = auth_client.delete(f"{BASE_URL}/api/customers/{cid}")
        assert r.status_code == 200


# ---------------- Suppliers ----------------
class TestSuppliers:
    def test_supplier_crud(self, auth_client):
        payload = {"name": "TEST_Supplier_1", "company": "TEST_Co",
                   "phone": "8888800001", "opening_balance": 1000}
        r = auth_client.post(f"{BASE_URL}/api/suppliers", json=payload)
        assert r.status_code == 200
        s = r.json()
        assert s["outstanding_amount"] == 1000
        sid = s["id"]

        r = auth_client.get(f"{BASE_URL}/api/suppliers")
        assert any(x["id"] == sid for x in r.json())

        upd = dict(payload)
        upd["phone"] = "8888800002"
        r = auth_client.put(f"{BASE_URL}/api/suppliers/{sid}", json=upd)
        assert r.status_code == 200
        assert r.json()["phone"] == "8888800002"

        r = auth_client.delete(f"{BASE_URL}/api/suppliers/{sid}")
        assert r.status_code == 200


# ---------------- Batches ----------------
class TestBatches:
    def test_batches_and_expiring(self, auth_client):
        # Create a product with expiry soon
        soon = "2026-06-01"
        p_soon = auth_client.post(f"{BASE_URL}/api/products", json={
            "name": "TEST_BATCH_SOON", "batch_number": "BS-1",
            "expiry_date": soon, "opening_stock": 5,
        }).json()

        p_far = auth_client.post(f"{BASE_URL}/api/products", json={
            "name": "TEST_BATCH_FAR", "batch_number": "BF-1",
            "expiry_date": "2099-01-01", "opening_stock": 5,
        }).json()

        try:
            r = auth_client.get(f"{BASE_URL}/api/batches")
            assert r.status_code == 200
            ids = [x["id"] for x in r.json()]
            assert p_soon["id"] in ids
            assert p_far["id"] in ids

            r = auth_client.get(f"{BASE_URL}/api/batches/expiring?days=365")
            assert r.status_code == 200
            ids = [x["id"] for x in r.json()]
            assert p_soon["id"] in ids
            assert p_far["id"] not in ids  # 2099 shouldn't be in expiring within 365 days
        finally:
            auth_client.delete(f"{BASE_URL}/api/products/{p_soon['id']}")
            auth_client.delete(f"{BASE_URL}/api/products/{p_far['id']}")


# ---------------- Dashboard ----------------
class TestDashboard:
    def test_dashboard_stats_shape(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/dashboard/stats")
        assert r.status_code == 200
        data = r.json()
        for key in ["total_products", "today_sales", "today_purchases",
                    "low_stock_count", "sales_trend", "top_selling",
                    "recent_sales", "recent_purchases",
                    "low_stock_products", "expiring_products"]:
            assert key in data, f"missing {key}"
        assert isinstance(data["sales_trend"], list)
        assert len(data["sales_trend"]) == 7
        for pt in data["sales_trend"]:
            assert "date" in pt and "total" in pt


# ---------------- Reports ----------------
class TestReports:
    def test_reports_summary_shape(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/reports/summary")
        assert r.status_code == 200
        data = r.json()
        for key in ["total_sales", "total_purchases", "total_profit",
                    "monthly", "category_wise", "tax",
                    "top_customers", "top_suppliers"]:
            assert key in data, f"missing {key}"
        assert isinstance(data["monthly"], list) and len(data["monthly"]) == 6
        assert "cgst" in data["tax"] and "sgst" in data["tax"]


# ---------------- Settings ----------------
class TestSettings:
    def test_get_and_update_settings(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/settings")
        assert r.status_code == 200
        data = r.json()
        assert "company_name" in data
        assert "invoice_prefix_sale" in data

        upd = dict(data)
        upd["company_name"] = "TEST_AgriStock_Co"
        upd["tax_rate"] = 7.5
        r = auth_client.put(f"{BASE_URL}/api/settings", json=upd)
        assert r.status_code == 200
        assert r.json()["company_name"] == "TEST_AgriStock_Co"
        assert r.json()["tax_rate"] == 7.5

        r = auth_client.get(f"{BASE_URL}/api/settings")
        assert r.json()["company_name"] == "TEST_AgriStock_Co"

        # revert
        upd["company_name"] = data.get("company_name", "AgriStock Pro")
        upd["tax_rate"] = data.get("tax_rate", 5.0)
        auth_client.put(f"{BASE_URL}/api/settings", json=upd)


# ---------------- Meta ----------------
class TestMeta:
    def test_next_invoice_sale(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/meta/next-invoice?kind=sale")
        assert r.status_code == 200
        assert "number" in r.json()
        assert r.json()["number"].startswith("INV-") or r.json()["number"]

    def test_next_invoice_purchase(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/meta/next-invoice?kind=purchase")
        assert r.status_code == 200
        num = r.json()["number"]
        assert num  # non-empty


# ---------------- End-to-End Purchase + Sale flow ----------------
class TestEndToEndFlow:
    def test_full_flow_stock_and_dues(self, auth_client):
        created = {"products": [], "customers": [], "suppliers": [],
                   "purchases": [], "sales": []}
        try:
            # 1. Supplier
            sup = auth_client.post(f"{BASE_URL}/api/suppliers", json={
                "name": "TEST_E2E_Supplier", "company": "E2E",
                "opening_balance": 0,
            }).json()
            created["suppliers"].append(sup["id"])

            # 2. Product with initial stock 20
            prod = auth_client.post(f"{BASE_URL}/api/products", json={
                "name": "TEST_E2E_Product", "category": "Fertilizer",
                "unit": "Bag", "purchase_price": 100, "selling_price": 150,
                "opening_stock": 20, "minimum_stock": 5,
            }).json()
            created["products"].append(prod["id"])
            assert prod["current_stock"] == 20

            # 3. Purchase posted -> stock +30, supplier due +1500
            purchase_body = {
                "supplier_id": sup["id"],
                "supplier_name": sup["name"],
                "invoice_number": "TEST-PUR-E2E-1",
                "invoice_date": "2026-01-15",
                "items": [{
                    "product_id": prod["id"], "product_name": prod["name"],
                    "unit": "Bag", "qty": 30, "unit_price": 100, "amount": 3000,
                }],
                "subtotal": 3000, "total": 3000,
                "paid_amount": 1500, "due_amount": 1500,
                "status": "posted",
            }
            r = auth_client.post(f"{BASE_URL}/api/purchases", json=purchase_body)
            assert r.status_code == 200, r.text
            created["purchases"].append(r.json()["id"])

            # verify product stock increased
            prod_after = auth_client.get(f"{BASE_URL}/api/products/{prod['id']}").json()
            assert prod_after["current_stock"] == 50, f"expected 50, got {prod_after['current_stock']}"

            # verify supplier outstanding increased
            sup_after = next(s for s in auth_client.get(f"{BASE_URL}/api/suppliers").json()
                             if s["id"] == sup["id"])
            assert sup_after["outstanding_amount"] == 1500

            # 4. Customer
            cust = auth_client.post(f"{BASE_URL}/api/customers", json={
                "name": "TEST_E2E_Customer", "opening_balance": 0,
            }).json()
            created["customers"].append(cust["id"])

            # 5. Sale posted, partially paid -> stock -10, customer due +500
            sale_body = {
                "customer_id": cust["id"], "customer_name": cust["name"],
                "invoice_number": "TEST-SAL-E2E-1",
                "invoice_date": "2026-01-15",
                "items": [{
                    "product_id": prod["id"], "product_name": prod["name"],
                    "unit": "Bag", "qty": 10, "unit_price": 150, "amount": 1500,
                }],
                "subtotal": 1500, "total": 1500,
                "received_amount": 1000, "payment_method": "Cash",
                "status": "posted",
            }
            r = auth_client.post(f"{BASE_URL}/api/sales", json=sale_body)
            assert r.status_code == 200, r.text
            created["sales"].append(r.json()["id"])

            prod_after2 = auth_client.get(f"{BASE_URL}/api/products/{prod['id']}").json()
            assert prod_after2["current_stock"] == 40, f"expected 40, got {prod_after2['current_stock']}"

            cust_after = next(c for c in auth_client.get(f"{BASE_URL}/api/customers").json()
                              if c["id"] == cust["id"])
            assert cust_after["current_due"] == 500, f"expected 500 due, got {cust_after['current_due']}"

            # 6. Delete sale -> stock should revert +10 (back to 50), customer due should revert -500 (back to 0)
            del_sale_res = auth_client.delete(f"{BASE_URL}/api/sales/{created['sales'][0]}")
            assert del_sale_res.status_code == 200
            created["sales"].pop(0)

            prod_after_sale_del = auth_client.get(f"{BASE_URL}/api/products/{prod['id']}").json()
            assert prod_after_sale_del["current_stock"] == 50, f"expected stock 50 after sale delete, got {prod_after_sale_del['current_stock']}"

            cust_after_sale_del = next(c for c in auth_client.get(f"{BASE_URL}/api/customers").json() if c["id"] == cust["id"])
            assert cust_after_sale_del["current_due"] == 0, f"expected due 0 after sale delete, got {cust_after_sale_del['current_due']}"

            # 7. Delete purchase -> stock should revert -30 (back to 20), supplier outstanding should revert -1500 (back to 0)
            del_pur_res = auth_client.delete(f"{BASE_URL}/api/purchases/{created['purchases'][0]}")
            assert del_pur_res.status_code == 200
            created["purchases"].pop(0)

            prod_after_pur_del = auth_client.get(f"{BASE_URL}/api/products/{prod['id']}").json()
            assert prod_after_pur_del["current_stock"] == 20, f"expected stock 20 after purchase delete, got {prod_after_pur_del['current_stock']}"

            sup_after_pur_del = next(s for s in auth_client.get(f"{BASE_URL}/api/suppliers").json() if s["id"] == sup["id"])
            assert sup_after_pur_del["outstanding_amount"] == 0, f"expected outstanding 0 after purchase delete, got {sup_after_pur_del['outstanding_amount']}"

        finally:
            for sid in created["sales"]:
                auth_client.delete(f"{BASE_URL}/api/sales/{sid}")
            for pid in created["purchases"]:
                auth_client.delete(f"{BASE_URL}/api/purchases/{pid}")
            for i in created["products"]:
                auth_client.delete(f"{BASE_URL}/api/products/{i}")
            for i in created["customers"]:
                auth_client.delete(f"{BASE_URL}/api/customers/{i}")
            for i in created["suppliers"]:
                auth_client.delete(f"{BASE_URL}/api/suppliers/{i}")

    def test_update_purchase_and_sale_put_endpoints(self, auth_client):
        created = {"products": [], "suppliers": [], "customers": [], "purchases": [], "sales": []}
        try:
            sup = auth_client.post(f"{BASE_URL}/api/suppliers", json={"name": "TEST_PUT_Supplier", "opening_balance": 0}).json()
            created["suppliers"].append(sup["id"])

            cust = auth_client.post(f"{BASE_URL}/api/customers", json={"name": "TEST_PUT_Customer", "opening_balance": 0}).json()
            created["customers"].append(cust["id"])

            prod = auth_client.post(f"{BASE_URL}/api/products", json={
                "name": "TEST_PUT_Prod", "category": "General", "unit": "Kg",
                "purchase_price": 50, "selling_price": 80, "opening_stock": 100
            }).json()
            created["products"].append(prod["id"])

            # Create Purchase
            pur = auth_client.post(f"{BASE_URL}/api/purchases", json={
                "supplier_id": sup["id"], "supplier_name": sup["name"],
                "invoice_number": "INV-PUT-P1", "invoice_date": "2026-01-01",
                "items": [{"product_id": prod["id"], "product_name": prod["name"], "qty": 10, "unit_price": 50, "tax_percent": 0, "amount": 500}],
                "subtotal": 500, "total": 500, "paid_amount": 300, "due_amount": 200, "status": "posted"
            }).json()
            created["purchases"].append(pur["id"])

            # PUT Purchase (update qty to 20)
            upd_pur_body = dict(pur)
            upd_pur_body["items"][0]["qty"] = 20
            upd_pur_body["subtotal"] = 1000
            upd_pur_body["total"] = 1000
            upd_pur_body["due_amount"] = 700
            r_put_pur = auth_client.put(f"{BASE_URL}/api/purchases/{pur['id']}", json=upd_pur_body)
            assert r_put_pur.status_code == 200
            assert r_put_pur.json()["total"] == 1000

            # Create Sale
            sale = auth_client.post(f"{BASE_URL}/api/sales", json={
                "customer_id": cust["id"], "customer_name": cust["name"],
                "invoice_number": "INV-PUT-S1", "invoice_date": "2026-01-01",
                "items": [{"product_id": prod["id"], "product_name": prod["name"], "qty": 5, "unit_price": 80, "tax_percent": 0, "amount": 400}],
                "subtotal": 400, "total": 400, "received_amount": 100, "status": "posted"
            }).json()
            created["sales"].append(sale["id"])

            # PUT Sale (update qty to 8)
            upd_sale_body = dict(sale)
            upd_sale_body["items"][0]["qty"] = 8
            upd_sale_body["subtotal"] = 640
            upd_sale_body["total"] = 640
            r_put_sale = auth_client.put(f"{BASE_URL}/api/sales/{sale['id']}", json=upd_sale_body)
            assert r_put_sale.status_code == 200
            assert r_put_sale.json()["total"] == 640
        finally:
            for sid in created["sales"]:
                auth_client.delete(f"{BASE_URL}/api/sales/{sid}")
            for pid in created["purchases"]:
                auth_client.delete(f"{BASE_URL}/api/purchases/{pid}")
            for i in created["products"]:
                auth_client.delete(f"{BASE_URL}/api/products/{i}")
            for i in created["customers"]:
                auth_client.delete(f"{BASE_URL}/api/customers/{i}")
            for i in created["suppliers"]:
                auth_client.delete(f"{BASE_URL}/api/suppliers/{i}")
