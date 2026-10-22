"""Database Schema DDL and SQL Constants for SQLite.

Defines tables for `invoices`, `invoice_items`, `invoice_audit_trail`, and `batch_jobs`
with referential integrity, cascading deletes, and optimized query indices.
"""

CREATE_INVOICES_TABLE = """
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    file_path TEXT,
    vendor_name TEXT NOT NULL,
    invoice_number TEXT,
    invoice_date TEXT,
    due_date TEXT,
    po_number TEXT,
    currency TEXT DEFAULT 'USD',
    subtotal REAL DEFAULT 0.0,
    tax_amount REAL DEFAULT 0.0,
    shipping_amount REAL DEFAULT 0.0,
    discount_amount REAL DEFAULT 0.0,
    total_amount REAL DEFAULT 0.0,
    amount_paid REAL DEFAULT 0.0,
    balance_due REAL DEFAULT 0.0,
    payment_terms TEXT,
    overall_confidence REAL DEFAULT 0.0,
    processing_status TEXT DEFAULT 'EXTRACTED',
    validation_status TEXT DEFAULT 'PENDING',
    raw_text TEXT,
    batch_id TEXT,
    is_duplicate INTEGER DEFAULT 0,
    duplicate_of_id INTEGER,
    duplicate_decision TEXT DEFAULT 'UNREVIEWED',
    reconciliation_status TEXT DEFAULT 'UNRECONCILED',
    reconciliation_notes TEXT,
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
    tax_amount REAL DEFAULT 0.0,
    discount_amount REAL DEFAULT 0.0,
    amount REAL DEFAULT 0.0,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
"""

CREATE_AUDIT_TRAIL_TABLE = """
CREATE TABLE IF NOT EXISTS invoice_audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    action TEXT DEFAULT 'USER_EDIT',
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
"""

CREATE_BATCH_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS batch_jobs (
    id TEXT PRIMARY KEY,
    total_files INTEGER DEFAULT 0,
    processed_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_invoices_vendor ON invoices(vendor_name);",
    "CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);",
    "CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);",
    "CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(validation_status);",
    "CREATE INDEX IF NOT EXISTS idx_invoices_reconcile ON invoices(reconciliation_status);",
    "CREATE INDEX IF NOT EXISTS idx_invoices_proc ON invoices(processing_status);",
    "CREATE INDEX IF NOT EXISTS idx_items_invoice_id ON invoice_items(invoice_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_invoice_id ON invoice_audit_trail(invoice_id);",
]
