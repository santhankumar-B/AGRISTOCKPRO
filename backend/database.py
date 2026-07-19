import asyncio
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

DB_PATH = os.path.abspath(os.environ.get("SQLITE_DB_PATH", os.path.join(os.path.dirname(__file__), "agristock.db")))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=60.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=60000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db():
    conn = _get_conn()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'cashier',
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'General',
            company TEXT NOT NULL DEFAULT '',
            brand TEXT NOT NULL DEFAULT '',
            barcode TEXT NOT NULL DEFAULT '',
            batch_number TEXT NOT NULL DEFAULT '',
            manufacture_date TEXT NOT NULL DEFAULT '',
            expiry_date TEXT NOT NULL DEFAULT '',
            unit TEXT NOT NULL DEFAULT 'Unit',
            purchase_price REAL NOT NULL DEFAULT 0.0,
            selling_price REAL NOT NULL DEFAULT 0.0,
            current_stock REAL NOT NULL DEFAULT 0.0,
            minimum_stock REAL NOT NULL DEFAULT 5.0,
            rack_number TEXT NOT NULL DEFAULT '',
            image_url TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            area TEXT NOT NULL DEFAULT '',
            gst TEXT NOT NULL DEFAULT '',
            credit_limit REAL NOT NULL DEFAULT 0.0,
            opening_balance REAL NOT NULL DEFAULT 0.0,
            current_due REAL NOT NULL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            company TEXT NOT NULL DEFAULT '',
            phone TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            gst TEXT NOT NULL DEFAULT '',
            bank_name TEXT NOT NULL DEFAULT '',
            bank_account TEXT NOT NULL DEFAULT '',
            ifsc TEXT NOT NULL DEFAULT '',
            opening_balance REAL NOT NULL DEFAULT 0.0,
            outstanding_amount REAL NOT NULL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS purchases (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            supplier_id TEXT NOT NULL DEFAULT '',
            supplier_name TEXT NOT NULL DEFAULT '',
            invoice_number TEXT NOT NULL,
            invoice_date TEXT NOT NULL,
            warehouse TEXT NOT NULL DEFAULT 'Main Warehouse',
            reference_number TEXT NOT NULL DEFAULT '',
            transporter TEXT NOT NULL DEFAULT '',
            payment_terms TEXT NOT NULL DEFAULT '',
            delivery_date TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            items_json TEXT NOT NULL DEFAULT '[]',
            subtotal REAL NOT NULL DEFAULT 0.0,
            discount REAL NOT NULL DEFAULT 0.0,
            cgst REAL NOT NULL DEFAULT 0.0,
            sgst REAL NOT NULL DEFAULT 0.0,
            total REAL NOT NULL DEFAULT 0.0,
            paid_amount REAL NOT NULL DEFAULT 0.0,
            due_amount REAL NOT NULL DEFAULT 0.0,
            payment_method TEXT NOT NULL DEFAULT 'Cash',
            status TEXT NOT NULL DEFAULT 'posted',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sales (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            customer_id TEXT NOT NULL DEFAULT '',
            customer_name TEXT NOT NULL DEFAULT '',
            customer_mobile TEXT NOT NULL DEFAULT '',
            billing_address TEXT NOT NULL DEFAULT '',
            invoice_number TEXT NOT NULL,
            invoice_date TEXT NOT NULL,
            due_date TEXT NOT NULL DEFAULT '',
            sales_person TEXT NOT NULL DEFAULT '',
            sales_type TEXT NOT NULL DEFAULT 'Direct Sale',
            payment_terms TEXT NOT NULL DEFAULT 'Cash',
            notes TEXT NOT NULL DEFAULT '',
            items_json TEXT NOT NULL DEFAULT '[]',
            subtotal REAL NOT NULL DEFAULT 0.0,
            discount REAL NOT NULL DEFAULT 0.0,
            cgst REAL NOT NULL DEFAULT 0.0,
            sgst REAL NOT NULL DEFAULT 0.0,
            total REAL NOT NULL DEFAULT 0.0,
            received_amount REAL NOT NULL DEFAULT 0.0,
            change_amount REAL NOT NULL DEFAULT 0.0,
            payment_method TEXT NOT NULL DEFAULT 'Cash',
            status TEXT NOT NULL DEFAULT 'posted',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            owner_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL DEFAULT 'AgriStock Pro Store',
            company_email TEXT NOT NULL DEFAULT 'contact@agristock.com',
            company_phone TEXT NOT NULL DEFAULT '+91 98765 43210',
            company_address TEXT NOT NULL DEFAULT 'Main Market, City',
            gst_number TEXT NOT NULL DEFAULT '33AAAAA0000A1Z5',
            currency TEXT NOT NULL DEFAULT 'INR',
            currency_symbol TEXT NOT NULL DEFAULT '₹',
            timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
            language TEXT NOT NULL DEFAULT 'en',
            invoice_prefix_sale TEXT NOT NULL DEFAULT 'INV-',
            invoice_prefix_purchase TEXT NOT NULL DEFAULT 'PUR-',
            logo_url TEXT NOT NULL DEFAULT '',
            tax_rate REAL NOT NULL DEFAULT 5.0,
            low_stock_alert INTEGER NOT NULL DEFAULT 10,
            expiry_alert_days INTEGER NOT NULL DEFAULT 30
        );

        CREATE TABLE IF NOT EXISTS counters (
            owner_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            seq INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (owner_id, kind)
        );
        """)
    conn.close()


def _row_to_dict(row: Optional[sqlite3.Row], json_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    d = dict(row)
    if json_fields:
        for f in json_fields:
            if f in d and isinstance(d[f], str):
                try:
                    target_key = f.replace("_json", "") if f.endswith("_json") else f
                    d[target_key] = json.loads(d[f])
                    if f != target_key:
                        d.pop(f, None)
                except Exception:
                    pass
    return d


# Async Database Helper Functions
async def execute(sql: str, params: tuple = ()) -> None:
    def _run():
        conn = _get_conn()
        with conn:
            conn.execute(sql, params)
        conn.close()
    await asyncio.to_thread(_run)


async def fetch_one(sql: str, params: tuple = (), json_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    def _run():
        conn = _get_conn()
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        conn.close()
        return _row_to_dict(row, json_fields)
    return await asyncio.to_thread(_run)


async def fetch_all(sql: str, params: tuple = (), json_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    def _run():
        conn = _get_conn()
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        conn.close()
        return [_row_to_dict(r, json_fields) for r in rows if r]
    return await asyncio.to_thread(_run)
