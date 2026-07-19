import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))
from database import init_db, execute

async def clear_all_sample_data():
    """
    Clears all sample inventory, purchases, sales, customers, and suppliers from agristock.db.
    Preserves user login accounts.
    """
    init_db()
    print("Clearing all sample products, purchases, sales, customers, and suppliers...")
    
    await execute("DELETE FROM products")
    await execute("DELETE FROM purchases")
    await execute("DELETE FROM sales")
    await execute("DELETE FROM customers")
    await execute("DELETE FROM suppliers")
    
    print("Database cleared successfully! Inventory, Purchases, Sales, Customers, and Suppliers are now 100% clean.")

if __name__ == "__main__":
    asyncio.run(clear_all_sample_data())
