"""Database Schema DDL and SQL Constants for SQLite.

Defines tables for `invoices` and `invoice_items` with referential integrity.
"""

CREATE_INVOICES_TABLE = """
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    vendor_name TEXT NOT NULL,
    invoice_number TEXT,
    invoice_date TEXT,
    due_date TEXT,
    currency TEXT DEFAULT 'USD',
    subtotal REAL DEFAULT 0.0,
    tax_amount REAL DEFAULT 0.0,
    shipping_amount REAL DEFAULT 0.0,
    discount_amount REAL DEFAULT 0.0,
    total_amount REAL DEFAULT 0.0,
    payment_terms TEXT,
    po_number TEXT,
    overall_confidence REAL DEFAULT 0.0,
    validation_status TEXT DEFAULT 'PENDING',
    raw_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_INVOICE_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity REAL DEFAULT 1.0,
    unit_price REAL DEFAULT 0.0,
    amount REAL DEFAULT 0.0,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_invoices_vendor ON invoices(vendor_name);",
    "CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);",
    "CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);",
    "CREATE INDEX IF NOT EXISTS idx_items_invoice_id ON invoice_items(invoice_id);",
]
