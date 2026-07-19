# AgriStock Pro 🌾🛒

**AgriStock Pro** is an enterprise-grade Billing, Inventory, and Financial Management application engineered specifically for agricultural retail stores, pesticide shops, fertilizer outlets, and seed distributors.

---

## ⚡ Highlights & Key Features

- **100% Offline Mode**: Runs locally with SQLite (WAL Mode). No internet connection or external MongoDB required.
- **1-Click Local Launcher**: Execute `start_offline.bat` to automatically spin up both backend and frontend servers with zero manual setup.
- **Double-Entry Financial Accounting**: Automated stock calculation, dues tracking, credit limits, and purchase/sales adjustments.
- **Invoice & GST Billing**: GST auto-breakdown (CGST/SGST), default 0% tax option, custom invoice numbering, auto-customer registration, and thermal print support.
- **Full Edit & Reversal Capability**: Edit existing Purchases and Sales with complete stock compensation and dues recalculation.
- **Batch & Expiry Management**: Low stock warnings, expiring inventory tracking, and batch alerts.
- **Multi-Tenant Data Isolation**: Secure role-based access control with rate-limiting and 5-attempt brute-force protection.

---

## 🚀 Quick Start (100% Offline)

### 1-Click Launch (Windows)
Double-click `start_offline.bat` in the repository root directory.
- Starts backend FastAPI server on `http://localhost:8000`
- Starts frontend React server on `http://localhost:3000`
- Opens your default web browser automatically!

---

## 💻 Tech Stack

- **Frontend**: React.js, Lucide Icons, Tailwind CSS, Recharts
- **Backend**: Python FastAPI, SQLite (Async via `to_thread`), Async Engine
- **Database**: SQLite WAL Mode (`agristock.db`)
- **Authentication**: JWT Cookies, Bcrypt Hashing, Failed Login Lockout Defense

---

## 📄 License
MIT License
