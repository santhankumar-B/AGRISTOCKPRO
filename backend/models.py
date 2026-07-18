"""Pydantic models for AgriStock Pro."""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid


def uid() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ORMBase(BaseModel):
    model_config = ConfigDict(extra="ignore")


# ---------------- Auth ----------------
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str


class UserOut(ORMBase):
    id: str
    username: str
    name: str
    role: str = "admin"
    created_at: str


# ---------------- Product ----------------
class ProductIn(BaseModel):
    name: str
    category: str = ""
    company: str = ""
    brand: str = ""
    barcode: str = ""
    batch_number: str = ""
    manufacture_date: str = ""
    expiry_date: str = ""
    unit: str = "Bag"
    purchase_price: float = 0
    selling_price: float = 0
    opening_stock: float = 0
    minimum_stock: float = 0
    rack_number: str = ""
    image_url: str = ""
    description: str = ""


class Product(ORMBase):
    id: str = Field(default_factory=uid)
    name: str
    category: str = ""
    company: str = ""
    brand: str = ""
    barcode: str = ""
    batch_number: str = ""
    manufacture_date: str = ""
    expiry_date: str = ""
    unit: str = "Bag"
    purchase_price: float = 0
    selling_price: float = 0
    current_stock: float = 0
    minimum_stock: float = 0
    rack_number: str = ""
    image_url: str = ""
    description: str = ""
    created_at: str = Field(default_factory=now_iso)


# ---------------- Customer ----------------
class CustomerIn(BaseModel):
    name: str
    phone: str = ""
    email: str = ""
    address: str = ""
    area: str = ""
    gst: str = ""
    credit_limit: float = 0
    opening_balance: float = 0
    status: str = "active"


class Customer(CustomerIn):
    id: str = Field(default_factory=uid)
    current_due: float = 0
    created_at: str = Field(default_factory=now_iso)


# ---------------- Supplier ----------------
class SupplierIn(BaseModel):
    name: str
    company: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    gst: str = ""
    bank_name: str = ""
    bank_account: str = ""
    ifsc: str = ""
    opening_balance: float = 0
    status: str = "active"


class Supplier(SupplierIn):
    id: str = Field(default_factory=uid)
    outstanding_amount: float = 0
    created_at: str = Field(default_factory=now_iso)


# ---------------- Purchase / Sales ----------------
class LineItem(BaseModel):
    product_id: str
    product_name: str
    barcode: str = ""
    batch_number: str = ""
    manufacture_date: str = ""
    expiry_date: str = ""
    unit: str = ""
    qty: float = 0
    unit_price: float = 0
    discount_percent: float = 0
    tax_percent: float = 0
    amount: float = 0


class PurchaseIn(BaseModel):
    supplier_id: str = ""
    supplier_name: str = ""
    invoice_number: str = ""
    invoice_date: str = ""
    warehouse: str = "Main Warehouse"
    reference_number: str = ""
    transporter: str = ""
    payment_terms: str = ""
    delivery_date: str = ""
    notes: str = ""
    items: List[LineItem] = []
    subtotal: float = 0
    discount: float = 0
    cgst: float = 0
    sgst: float = 0
    total: float = 0
    paid_amount: float = 0
    due_amount: float = 0
    payment_method: str = ""
    status: str = "posted"


class Purchase(PurchaseIn):
    id: str = Field(default_factory=uid)
    created_at: str = Field(default_factory=now_iso)


class SaleIn(BaseModel):
    customer_id: str = ""
    customer_name: str = ""
    customer_mobile: str = ""
    billing_address: str = ""
    invoice_number: str = ""
    invoice_date: str = ""
    due_date: str = ""
    sales_person: str = ""
    sales_type: str = "Direct Sale"
    payment_terms: str = "Cash"
    notes: str = ""
    items: List[LineItem] = []
    subtotal: float = 0
    discount: float = 0
    cgst: float = 0
    sgst: float = 0
    total: float = 0
    received_amount: float = 0
    change_amount: float = 0
    payment_method: str = "Cash"
    status: str = "posted"


class Sale(SaleIn):
    id: str = Field(default_factory=uid)
    created_at: str = Field(default_factory=now_iso)


# ---------------- Settings ----------------
class Settings(BaseModel):
    company_name: str = "AgriStock Pro"
    company_email: str = ""
    company_phone: str = ""
    company_address: str = ""
    gst_number: str = ""
    currency: str = "INR"
    currency_symbol: str = "₹"
    timezone: str = "Asia/Kolkata"
    language: str = "English"
    invoice_prefix_sale: str = "INV-"
    invoice_prefix_purchase: str = "PUR-"
    logo_url: str = ""
    tax_rate: float = 5.0
    low_stock_alert: bool = True
    expiry_alert_days: int = 90
