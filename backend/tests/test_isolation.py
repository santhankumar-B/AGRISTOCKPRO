"""Per-user data isolation tests (Layer-3 object-level ownership).

Verifies that every domain resource is scoped by owner_id and that a
user's data is completely invisible to other users. Also probes IDOR/BOLA
and server-stamped ownership.
"""
import os
import time
import uuid
import requests
import pytest
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / "frontend" / ".env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")


# ---------- helpers ----------
def _login(username: str, password: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    assert r.status_code == 200, f"Login failed for {username}: {r.status_code} {r.text}"
    data = r.json()
    s.headers["Authorization"] = f"Bearer {data['token']}"
    s._user = data["user"]  # attach for convenience
    return s


@pytest.fixture(scope="module")
def u1():
    return _login("user1", "user@123")


@pytest.fixture(scope="module")
def u2():
    return _login("user2", "user@123")


@pytest.fixture(scope="module")
def admin():
    return _login("admin", "admin123")


def _tag():
    """Unique tag per test-run so parallel/repeated runs don't collide."""
    return f"ISO_{uuid.uuid4().hex[:8]}"


# =========================================================
# 1) Products isolation
# =========================================================
class TestProductIsolation:
    def test_products_are_isolated_between_users(self, u1, u2):
        tag = _tag()
        # user1 creates a product
        r = u1.post(f"{BASE_URL}/api/products", json={
            "name": f"TEST_{tag}_U1_PROD", "opening_stock": 10, "minimum_stock": 1,
        })
        assert r.status_code == 200, r.text
        p1 = r.json()

        # user2 must NOT see user1's product in list
        r = u2.get(f"{BASE_URL}/api/products")
        assert r.status_code == 200
        u2_names = {x["name"] for x in r.json()}
        assert p1["name"] not in u2_names, "LEAK: user2 saw user1's product in list"

        # user2 direct GET must be 404 (NOT 403 — 403 leaks existence)
        r = u2.get(f"{BASE_URL}/api/products/{p1['id']}")
        assert r.status_code == 404, f"IDOR: expected 404, got {r.status_code}"

        # user2 PUT on user1's product -> 404
        r = u2.put(f"{BASE_URL}/api/products/{p1['id']}", json={
            "name": "HACKED", "opening_stock": 0, "minimum_stock": 0,
        })
        assert r.status_code == 404, f"IDOR PUT: expected 404, got {r.status_code}"

        # verify user1's product unchanged
        r = u1.get(f"{BASE_URL}/api/products/{p1['id']}")
        assert r.status_code == 200
        assert r.json()["name"] == p1["name"]

        # user2 DELETE on user1's product -> 404
        r = u2.delete(f"{BASE_URL}/api/products/{p1['id']}")
        assert r.status_code == 404, f"IDOR DELETE: expected 404, got {r.status_code}"

        # user1 can still see & delete their own
        r = u1.delete(f"{BASE_URL}/api/products/{p1['id']}")
        assert r.status_code == 200

    def test_mass_assign_owner_id_is_ignored(self, u1, u2):
        """user1 tries to set owner_id=user2 on POST — must be silently overridden."""
        tag = _tag()
        u2_id = u2._user["id"]
        r = u1.post(f"{BASE_URL}/api/products", json={
            "name": f"TEST_{tag}_MASSASSIGN", "opening_stock": 1, "minimum_stock": 0,
            "owner_id": u2_id,  # attempted mass-assign
        })
        assert r.status_code == 200, r.text
        p = r.json()
        try:
            # user2 must NOT see it
            names_u2 = {x["name"] for x in u2.get(f"{BASE_URL}/api/products").json()}
            assert p["name"] not in names_u2, "LEAK: mass-assigned owner_id honored — user2 saw product"

            # user1 must see it
            names_u1 = {x["name"] for x in u1.get(f"{BASE_URL}/api/products").json()}
            assert p["name"] in names_u1, "user1 doesn't own their own creation"
        finally:
            u1.delete(f"{BASE_URL}/api/products/{p['id']}")


# =========================================================
# 2) Customers isolation
# =========================================================
class TestCustomerIsolation:
    def test_customer_isolation_and_idor(self, u1, u2):
        tag = _tag()
        r = u1.post(f"{BASE_URL}/api/customers", json={
            "name": f"TEST_{tag}_U1_CUST", "opening_balance": 100,
        })
        assert r.status_code == 200
        c1 = r.json()

        # user2 list should not include it
        u2_names = {x["name"] for x in u2.get(f"{BASE_URL}/api/customers").json()}
        assert c1["name"] not in u2_names

        # IDOR: PUT/DELETE by user2 -> 404
        r = u2.put(f"{BASE_URL}/api/customers/{c1['id']}", json={
            "name": "HACKED", "opening_balance": 0,
        })
        assert r.status_code == 404
        r = u2.delete(f"{BASE_URL}/api/customers/{c1['id']}")
        assert r.status_code == 404

        # cleanup
        u1.delete(f"{BASE_URL}/api/customers/{c1['id']}")


# =========================================================
# 3) Suppliers isolation
# =========================================================
class TestSupplierIsolation:
    def test_supplier_isolation_and_idor(self, u1, u2):
        tag = _tag()
        r = u1.post(f"{BASE_URL}/api/suppliers", json={
            "name": f"TEST_{tag}_U1_SUP", "opening_balance": 500,
        })
        assert r.status_code == 200
        s1 = r.json()

        u2_names = {x["name"] for x in u2.get(f"{BASE_URL}/api/suppliers").json()}
        assert s1["name"] not in u2_names

        r = u2.put(f"{BASE_URL}/api/suppliers/{s1['id']}", json={
            "name": "HACKED", "opening_balance": 0,
        })
        assert r.status_code == 404
        r = u2.delete(f"{BASE_URL}/api/suppliers/{s1['id']}")
        assert r.status_code == 404

        u1.delete(f"{BASE_URL}/api/suppliers/{s1['id']}")


# =========================================================
# 4) Purchases isolation + stock isolation
# =========================================================
class TestPurchaseIsolation:
    def test_purchase_isolation_and_stock_scoped(self, u1, u2):
        tag = _tag()
        # Both users create a product with the SAME name to prove stock update is scoped by owner
        prod_u1 = u1.post(f"{BASE_URL}/api/products", json={
            "name": f"TEST_{tag}_SHARED_NAME", "opening_stock": 10, "minimum_stock": 1,
        }).json()
        prod_u2 = u2.post(f"{BASE_URL}/api/products", json={
            "name": f"TEST_{tag}_SHARED_NAME", "opening_stock": 10, "minimum_stock": 1,
        }).json()
        assert prod_u1["id"] != prod_u2["id"]

        purchase_ids = []
        try:
            # user1 posts a purchase for 25 units of their product
            r = u1.post(f"{BASE_URL}/api/purchases", json={
                "supplier_name": "TEST_SUP",
                "invoice_number": f"TEST-{tag}-PUR-1",
                "invoice_date": "2026-01-15",
                "items": [{
                    "product_id": prod_u1["id"],
                    "product_name": prod_u1["name"],
                    "unit": "Bag", "qty": 25, "unit_price": 10, "amount": 250,
                }],
                "subtotal": 250, "total": 250, "paid_amount": 250, "due_amount": 0,
                "status": "posted",
            })
            assert r.status_code == 200, r.text
            purchase_ids.append(("u1", r.json()["id"]))

            # user1's product stock should be 35
            p_after_u1 = u1.get(f"{BASE_URL}/api/products/{prod_u1['id']}").json()
            assert p_after_u1["current_stock"] == 35, f"expected 35 got {p_after_u1['current_stock']}"

            # user2's identically-named product stock must still be 10
            p_after_u2 = u2.get(f"{BASE_URL}/api/products/{prod_u2['id']}").json()
            assert p_after_u2["current_stock"] == 10, (
                f"LEAK: user1's purchase touched user2's product stock: {p_after_u2['current_stock']}"
            )

            # user2 must not see user1's purchase
            u2_invs = {x["invoice_number"] for x in u2.get(f"{BASE_URL}/api/purchases").json()}
            assert f"TEST-{tag}-PUR-1" not in u2_invs

            # IDOR: user2 GET / DELETE user1's purchase -> 404
            u1_purchase_id = purchase_ids[0][1]
            r = u2.get(f"{BASE_URL}/api/purchases/{u1_purchase_id}")
            assert r.status_code == 404
            r = u2.delete(f"{BASE_URL}/api/purchases/{u1_purchase_id}")
            assert r.status_code == 404
        finally:
            for who, pid in purchase_ids:
                (u1 if who == "u1" else u2).delete(f"{BASE_URL}/api/purchases/{pid}")
            u1.delete(f"{BASE_URL}/api/products/{prod_u1['id']}")
            u2.delete(f"{BASE_URL}/api/products/{prod_u2['id']}")


# =========================================================
# 5) Sales isolation + stock isolation
# =========================================================
class TestSaleIsolation:
    def test_sale_isolation_and_stock_scoped(self, u1, u2):
        tag = _tag()
        prod_u1 = u1.post(f"{BASE_URL}/api/products", json={
            "name": f"TEST_{tag}_SALE_NAME", "opening_stock": 50, "minimum_stock": 1,
        }).json()
        prod_u2 = u2.post(f"{BASE_URL}/api/products", json={
            "name": f"TEST_{tag}_SALE_NAME", "opening_stock": 50, "minimum_stock": 1,
        }).json()

        sale_ids = []
        try:
            r = u1.post(f"{BASE_URL}/api/sales", json={
                "customer_name": "TEST_CUST",
                "invoice_number": f"TEST-{tag}-SAL-1",
                "invoice_date": "2026-01-15",
                "items": [{
                    "product_id": prod_u1["id"],
                    "product_name": prod_u1["name"],
                    "unit": "Bag", "qty": 15, "unit_price": 20, "amount": 300,
                }],
                "subtotal": 300, "total": 300, "received_amount": 300,
                "status": "posted",
            })
            assert r.status_code == 200, r.text
            sale_ids.append(("u1", r.json()["id"]))

            # user1's stock 50 - 15 = 35
            assert u1.get(f"{BASE_URL}/api/products/{prod_u1['id']}").json()["current_stock"] == 35
            # user2's identically-named product stock untouched
            assert u2.get(f"{BASE_URL}/api/products/{prod_u2['id']}").json()["current_stock"] == 50

            # user2 cannot see user1's sale
            u2_invs = {x["invoice_number"] for x in u2.get(f"{BASE_URL}/api/sales").json()}
            assert f"TEST-{tag}-SAL-1" not in u2_invs

            u1_sale_id = sale_ids[0][1]
            assert u2.get(f"{BASE_URL}/api/sales/{u1_sale_id}").status_code == 404
            assert u2.delete(f"{BASE_URL}/api/sales/{u1_sale_id}").status_code == 404
        finally:
            for who, sid in sale_ids:
                (u1 if who == "u1" else u2).delete(f"{BASE_URL}/api/sales/{sid}")
            u1.delete(f"{BASE_URL}/api/products/{prod_u1['id']}")
            u2.delete(f"{BASE_URL}/api/products/{prod_u2['id']}")


# =========================================================
# 6) Settings isolation
# =========================================================
class TestSettingsIsolation:
    def test_settings_are_per_user(self, u1, u2):
        # Read both users' settings
        s1_before = u1.get(f"{BASE_URL}/api/settings").json()
        _ = u2.get(f"{BASE_URL}/api/settings").json()

        # user1 sets a unique company name
        unique_name_u1 = f"TEST_U1_CO_{uuid.uuid4().hex[:6]}"
        upd = dict(s1_before)
        upd["company_name"] = unique_name_u1
        r = u1.put(f"{BASE_URL}/api/settings", json=upd)
        assert r.status_code == 200
        assert r.json()["company_name"] == unique_name_u1

        # user2's settings must not have that value
        s2_after = u2.get(f"{BASE_URL}/api/settings").json()
        assert s2_after["company_name"] != unique_name_u1, (
            "LEAK: user1's settings change bled into user2"
        )

        # user1 GET returns their own updated doc
        s1_after = u1.get(f"{BASE_URL}/api/settings").json()
        assert s1_after["company_name"] == unique_name_u1

        # cleanup: restore user1 settings
        upd["company_name"] = s1_before.get("company_name", "AgriStock Pro")
        u1.put(f"{BASE_URL}/api/settings", json=upd)


# =========================================================
# 7) Meta / next-invoice per-user
# =========================================================
class TestMetaInvoiceIsolation:
    def test_next_invoice_is_per_user(self, u1, u2):
        # Get initial counters
        u1_next_before = u1.get(f"{BASE_URL}/api/meta/next-invoice?kind=sale").json()["number"]
        u2_next_before = u2.get(f"{BASE_URL}/api/meta/next-invoice?kind=sale").json()["number"]

        # Both should be valid strings
        assert u1_next_before and u2_next_before

        # user1 creates 2 sales
        created = []
        try:
            for i in range(2):
                r = u1.post(f"{BASE_URL}/api/sales", json={
                    "invoice_number": f"TEST-META-{uuid.uuid4().hex[:6]}",
                    "invoice_date": "2026-01-15",
                    "items": [], "subtotal": 0, "total": 0, "received_amount": 0,
                    "status": "posted",
                })
                assert r.status_code == 200
                created.append(r.json()["id"])

            u1_next_after = u1.get(f"{BASE_URL}/api/meta/next-invoice?kind=sale").json()["number"]
            u2_next_after = u2.get(f"{BASE_URL}/api/meta/next-invoice?kind=sale").json()["number"]

            # user1's next-invoice must advance
            assert u1_next_after != u1_next_before, (
                f"user1 next-invoice did not advance: before={u1_next_before} after={u1_next_after}"
            )
            # user2's must NOT have changed
            assert u2_next_after == u2_next_before, (
                f"LEAK: user2 next-invoice changed after user1 created sales: "
                f"before={u2_next_before} after={u2_next_after}"
            )
        finally:
            for sid in created:
                u1.delete(f"{BASE_URL}/api/sales/{sid}")


# =========================================================
# 8) Dashboard / Reports / Batches isolation
# =========================================================
class TestDashboardReportsBatchesIsolation:
    def test_dashboard_totals_are_per_user(self, u1, u2):
        tag = _tag()
        # Baseline
        d2_before = u2.get(f"{BASE_URL}/api/dashboard/stats").json()

        # user1 creates a product with a batch/expiry + a posted sale
        prod = u1.post(f"{BASE_URL}/api/products", json={
            "name": f"TEST_{tag}_DASH", "opening_stock": 5, "minimum_stock": 1,
            "batch_number": "B1", "expiry_date": "2026-06-01",
            "purchase_price": 10, "selling_price": 20,
        }).json()
        sale_ids = []
        try:
            r = u1.post(f"{BASE_URL}/api/sales", json={
                "customer_name": "TEST_DASH",
                "invoice_number": f"TEST-{tag}-DSAL",
                "invoice_date": "2026-01-15",
                "items": [{
                    "product_id": prod["id"], "product_name": prod["name"],
                    "unit": "Bag", "qty": 2, "unit_price": 20, "amount": 40,
                }],
                "subtotal": 40, "total": 40, "received_amount": 40, "status": "posted",
            })
            assert r.status_code == 200
            sale_ids.append(r.json()["id"])

            # dashboard for user1 should count the product
            d1 = u1.get(f"{BASE_URL}/api/dashboard/stats").json()
            assert d1["total_products"] >= 1

            # dashboard for user2 should not include user1's product or sale
            d2_after = u2.get(f"{BASE_URL}/api/dashboard/stats").json()
            u2_prods = u2.get(f"{BASE_URL}/api/products").json()
            assert prod["id"] not in [p["id"] for p in u2_prods], "LEAK: user2 saw user1 product"
            assert d2_after["total_sales"] == d2_before["total_sales"], "LEAK: user2 total_sales changed"

            # Reports
            r1 = u1.get(f"{BASE_URL}/api/reports/summary").json()
            r2 = u2.get(f"{BASE_URL}/api/reports/summary").json()
            assert r1["sales_count"] >= 1
            # user2's should not include user1's sale total
            names_u2 = {t["name"] for t in r2.get("top_customers", [])}
            assert "TEST_DASH" not in names_u2

            # Batches
            b1_ids = {b["id"] for b in u1.get(f"{BASE_URL}/api/batches").json()}
            b2_ids = {b["id"] for b in u2.get(f"{BASE_URL}/api/batches").json()}
            assert prod["id"] in b1_ids
            assert prod["id"] not in b2_ids, "LEAK: user2 saw user1 batch"

            # Expiring — 2026-06-01 within 365 days
            e1_ids = {b["id"] for b in u1.get(f"{BASE_URL}/api/batches/expiring?days=365").json()}
            e2_ids = {b["id"] for b in u2.get(f"{BASE_URL}/api/batches/expiring?days=365").json()}
            assert prod["id"] in e1_ids
            assert prod["id"] not in e2_ids
        finally:
            for sid in sale_ids:
                u1.delete(f"{BASE_URL}/api/sales/{sid}")
            u1.delete(f"{BASE_URL}/api/products/{prod['id']}")


# =========================================================
# 9) Admin isolation — admin is just another owner
# =========================================================
class TestAdminIsolation:
    def test_admin_does_not_see_user_data(self, u1, admin):
        tag = _tag()
        p = u1.post(f"{BASE_URL}/api/products", json={
            "name": f"TEST_{tag}_ADMIN_CHECK", "opening_stock": 1, "minimum_stock": 0,
        }).json()
        try:
            admin_names = {x["name"] for x in admin.get(f"{BASE_URL}/api/products").json()}
            assert p["name"] not in admin_names, (
                "LEAK: admin sees user1's product (admin should be its own workspace)"
            )
            # admin GET direct -> 404
            assert admin.get(f"{BASE_URL}/api/products/{p['id']}").status_code == 404
        finally:
            u1.delete(f"{BASE_URL}/api/products/{p['id']}")
