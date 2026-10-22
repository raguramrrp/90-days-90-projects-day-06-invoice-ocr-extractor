"""Database Repository for Invoices, Line Items, and Audit History.

Provides thread-safe persistence, search, filtering, duplicate matching,
and audit trail tracking using standard library sqlite3 with foreign key enforcement.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import config
from src.database.models import (
    CREATE_AUDIT_TRAIL_TABLE,
    CREATE_BATCH_JOBS_TABLE,
    CREATE_INDEXES,
    CREATE_INVOICE_ITEMS_TABLE,
    CREATE_INVOICES_TABLE,
)


class InvoiceRepository:
    """Handles persistence and retrieval of structured invoices in SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize repository with target database path."""
        self.db_path = Path(db_path or config.DATABASE_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a database connection with foreign key support and dict-like row access."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self) -> None:
        """Create tables and performance indices if they do not exist, and safely migrate columns."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(CREATE_INVOICES_TABLE)
            cursor.execute(CREATE_INVOICE_ITEMS_TABLE)
            cursor.execute(CREATE_AUDIT_TRAIL_TABLE)
            cursor.execute(CREATE_BATCH_JOBS_TABLE)

            # Safe column migration for existing databases
            cursor.execute("PRAGMA table_info(invoices);")
            existing_cols = {row["name"] for row in cursor.fetchall()}

            new_columns = [
                ("amount_paid", "REAL DEFAULT 0.0"),
                ("balance_due", "REAL DEFAULT 0.0"),
                ("file_path", "TEXT"),
                ("batch_id", "TEXT"),
                ("is_duplicate", "INTEGER DEFAULT 0"),
                ("duplicate_of_id", "INTEGER"),
                ("processing_status", "TEXT DEFAULT 'EXTRACTED'"),
                ("duplicate_decision", "TEXT DEFAULT 'UNREVIEWED'"),
                ("reconciliation_status", "TEXT DEFAULT 'UNRECONCILED'"),
                ("reconciliation_notes", "TEXT"),
            ]
            for col_name, col_type in new_columns:
                if col_name not in existing_cols:
                    try:
                        cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type};")
                    except Exception:
                        pass

            # Safe column migration for existing databases: invoice_items table
            cursor.execute("PRAGMA table_info(invoice_items);")
            existing_item_cols = {row["name"] for row in cursor.fetchall()}
            new_item_columns = [
                ("tax_amount", "REAL DEFAULT 0.0"),
                ("discount_amount", "REAL DEFAULT 0.0"),
            ]
            for col_name, col_type in new_item_columns:
                if col_name not in existing_item_cols:
                    try:
                        cursor.execute(f"ALTER TABLE invoice_items ADD COLUMN {col_name} {col_type};")
                    except Exception:
                        pass

            for idx in CREATE_INDEXES:
                cursor.execute(idx)
            conn.commit()

    def save_invoice(
        self,
        invoice_data: Dict[str, Any],
        items: Optional[List[Dict[str, Any]]] = None,
        filename: Optional[str] = None,
    ) -> int:
        """Save a new invoice record and its associated line items in an atomic transaction."""
        items_list = items if items is not None else invoice_data.get("line_items", [])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO invoices (
                    filename, file_path, vendor_name, invoice_number, invoice_date, due_date,
                    po_number, currency, subtotal, tax_amount, shipping_amount, discount_amount,
                    total_amount, amount_paid, balance_due, payment_terms, overall_confidence,
                    processing_status, validation_status, raw_text, batch_id, is_duplicate, duplicate_of_id,
                    duplicate_decision, reconciliation_status, reconciliation_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    filename or invoice_data.get("filename"),
                    invoice_data.get("file_path"),
                    invoice_data.get("vendor_name", "Unknown Vendor"),
                    invoice_data.get("invoice_number", "N/A"),
                    invoice_data.get("invoice_date"),
                    invoice_data.get("due_date"),
                    invoice_data.get("po_number"),
                    invoice_data.get("currency", "USD"),
                    float(invoice_data.get("subtotal", 0.0) or 0.0),
                    float(invoice_data.get("tax_amount", 0.0) or 0.0),
                    float(invoice_data.get("shipping_amount", 0.0) or 0.0),
                    float(invoice_data.get("discount_amount", 0.0) or 0.0),
                    float(invoice_data.get("total_amount", 0.0) or 0.0),
                    float(invoice_data.get("amount_paid", 0.0) or 0.0),
                    float(invoice_data.get("balance_due", 0.0) or 0.0),
                    invoice_data.get("payment_terms"),
                    float(invoice_data.get("overall_confidence", 0.0) or 0.0),
                    invoice_data.get("processing_status", "EXTRACTED"),
                    invoice_data.get("validation_status", "PENDING"),
                    invoice_data.get("raw_text", ""),
                    invoice_data.get("batch_id"),
                    int(invoice_data.get("is_duplicate", 0) or 0),
                    invoice_data.get("duplicate_of_id"),
                    invoice_data.get("duplicate_decision", "UNREVIEWED"),
                    invoice_data.get("reconciliation_status", "UNRECONCILED"),
                    invoice_data.get("reconciliation_notes"),
                ),
            )
            invoice_id = cursor.lastrowid

            if items_list:
                for item in items_list:
                    cursor.execute(
                        """
                        INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, tax_amount, discount_amount, amount)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            invoice_id,
                            item.get("description", "Item"),
                            float(item.get("quantity", 1.0) or 1.0),
                            float(item.get("unit_price", 0.0) or 0.0),
                            float(item.get("tax_amount", 0.0) or 0.0),
                            float(item.get("discount_amount", 0.0) or 0.0),
                            float(item.get("amount", 0.0) or 0.0),
                        ),
                    )

            # Record initial audit entry
            cursor.execute(
                """
                INSERT INTO invoice_audit_trail (invoice_id, field_name, old_value, new_value, action)
                VALUES (?, ?, ?, ?, ?)
                """,
                (invoice_id, "RECORD_CREATED", None, f"Initial extraction from {filename or 'document'}", "CREATION"),
            )

            conn.commit()
            return int(invoice_id)

    def log_audit_entry(
        self,
        invoice_id: int,
        field_name: str,
        old_value: Optional[str],
        new_value: Optional[str],
        action: str = "USER_EDIT",
    ) -> None:
        """Record an explicit change in the invoice audit trail."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO invoice_audit_trail (invoice_id, field_name, old_value, new_value, action)
                VALUES (?, ?, ?, ?, ?)
                """,
                (invoice_id, field_name, str(old_value) if old_value is not None else None, str(new_value) if new_value is not None else None, action),
            )
            conn.commit()

    def get_audit_trail(self, invoice_id: int) -> List[Dict[str, Any]]:
        """Retrieve historical audit logs for a given invoice."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM invoice_audit_trail WHERE invoice_id = ? ORDER BY changed_at DESC",
                (invoice_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_invoices(
        self,
        search_query: Optional[str] = None,
        vendor: Optional[str] = None,
        status: Optional[str] = None,
        currency: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "DESC",
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Retrieve invoices matching advanced search queries, date ranges, and sorting."""
        query = "SELECT * FROM invoices WHERE 1=1"
        params: List[Any] = []

        if search_query:
            query += " AND (vendor_name LIKE ? OR invoice_number LIKE ? OR po_number LIKE ?)"
            pattern = f"%{search_query.strip()}%"
            params.extend([pattern, pattern, pattern])

        if vendor and vendor != "All":
            query += " AND vendor_name = ?"
            params.append(vendor)

        if status and status != "All":
            query += " AND validation_status = ?"
            params.append(status)

        if currency and currency != "All":
            query += " AND currency = ?"
            params.append(currency)

        if date_from:
            query += " AND invoice_date >= ?"
            params.append(date_from)

        if date_to:
            query += " AND invoice_date <= ?"
            params.append(date_to)

        # Validate sort field to prevent SQL injection
        allowed_sort = {
            "created_at": "created_at",
            "invoice_date": "invoice_date",
            "total_amount": "total_amount",
            "vendor_name": "vendor_name",
            "invoice_number": "invoice_number",
        }
        order_col = allowed_sort.get(sort_by, "created_at")
        direction = "ASC" if sort_order.upper() == "ASC" else "DESC"

        query += f" ORDER BY {order_col} {direction} LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific invoice, its items, and its audit history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
            inv_row = cursor.fetchone()
            if not inv_row:
                return None

            inv_dict = dict(inv_row)

            cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            items_rows = cursor.fetchall()
            inv_dict["line_items"] = [dict(item) for item in items_rows]

            cursor.execute("SELECT * FROM invoice_audit_trail WHERE invoice_id = ? ORDER BY changed_at DESC", (invoice_id,))
            inv_dict["audit_trail"] = [dict(a) for a in cursor.fetchall()]

            return inv_dict

    def update_invoice(
        self,
        invoice_id: int,
        invoice_data: Dict[str, Any],
        items: Optional[List[Dict[str, Any]]] = None,
        action_note: str = "USER_EDIT",
    ) -> bool:
        """Update an existing invoice record, track changes in audit trail, and re-sync line items."""
        # Fetch current record to log field-level diffs
        current = self.get_invoice_by_id(invoice_id)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE invoices SET
                    vendor_name = ?,
                    invoice_number = ?,
                    invoice_date = ?,
                    due_date = ?,
                    po_number = ?,
                    currency = ?,
                    subtotal = ?,
                    tax_amount = ?,
                    shipping_amount = ?,
                    discount_amount = ?,
                    total_amount = ?,
                    amount_paid = ?,
                    balance_due = ?,
                    payment_terms = ?,
                    validation_status = ?,
                    processing_status = ?,
                    duplicate_decision = ?,
                    reconciliation_status = ?,
                    reconciliation_notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    invoice_data.get("vendor_name", "Unknown Vendor"),
                    invoice_data.get("invoice_number", "N/A"),
                    invoice_data.get("invoice_date"),
                    invoice_data.get("due_date"),
                    invoice_data.get("po_number"),
                    invoice_data.get("currency", "USD"),
                    float(invoice_data.get("subtotal", 0.0) or 0.0),
                    float(invoice_data.get("tax_amount", 0.0) or 0.0),
                    float(invoice_data.get("shipping_amount", 0.0) or 0.0),
                    float(invoice_data.get("discount_amount", 0.0) or 0.0),
                    float(invoice_data.get("total_amount", 0.0) or 0.0),
                    float(invoice_data.get("amount_paid", 0.0) or 0.0),
                    float(invoice_data.get("balance_due", 0.0) or 0.0),
                    invoice_data.get("payment_terms"),
                    invoice_data.get("validation_status", "VALIDATED"),
                    invoice_data.get("processing_status", "VALIDATED"),
                    invoice_data.get("duplicate_decision", "UNREVIEWED"),
                    invoice_data.get("reconciliation_status", "UNRECONCILED"),
                    invoice_data.get("reconciliation_notes"),
                    invoice_id,
                ),
            )

            # Log audit trail diffs
            if current:
                diff_fields = ["vendor_name", "invoice_number", "total_amount", "invoice_date", "due_date"]
                for f in diff_fields:
                    old_v = current.get(f)
                    new_v = invoice_data.get(f)
                    if str(old_v) != str(new_v):
                        cursor.execute(
                            """
                            INSERT INTO invoice_audit_trail (invoice_id, field_name, old_value, new_value, action)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (invoice_id, f, str(old_v), str(new_v), action_note),
                        )

            if items is not None:
                cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
                for item in items:
                    cursor.execute(
                        """
                        INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, tax_amount, discount_amount, amount)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            invoice_id,
                            item.get("description", "Item"),
                            float(item.get("quantity", 1.0) or 1.0),
                            float(item.get("unit_price", 0.0) or 0.0),
                            float(item.get("tax_amount", 0.0) or 0.0),
                            float(item.get("discount_amount", 0.0) or 0.0),
                            float(item.get("amount", 0.0) or 0.0),
                        ),
                    )

            conn.commit()
            return cursor.rowcount > 0

    def delete_invoice(self, invoice_id: int) -> bool:
        """Delete an invoice record (cascading deletes line items and audit trail)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Aggregate summary metrics for executive dashboards."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_invoices,
                    COALESCE(SUM(total_amount), 0.0) as total_spend,
                    COALESCE(AVG(total_amount), 0.0) as avg_amount
                FROM invoices
                """
            )
            totals = dict(cursor.fetchone())

            cursor.execute(
                """
                SELECT
                    currency,
                    COUNT(*) as count,
                    COALESCE(SUM(total_amount), 0.0) as total
                FROM invoices
                GROUP BY currency
                """
            )
            currency_totals = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT
                    vendor_name,
                    COUNT(*) as invoice_count,
                    COALESCE(SUM(total_amount), 0.0) as total_spent
                FROM invoices
                GROUP BY vendor_name
                ORDER BY total_spent DESC
                LIMIT 8
                """
            )
            top_vendors = [dict(row) for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT validation_status, COUNT(*) as count
                FROM invoices
                GROUP BY validation_status
                """
            )
            status_breakdown = {row["validation_status"]: row["count"] for row in cursor.fetchall()}

            # Monthly spend trend
            cursor.execute(
                """
                SELECT
                    SUBSTR(COALESCE(invoice_date, created_at), 1, 7) as month_str,
                    COUNT(*) as invoice_count,
                    COALESCE(SUM(total_amount), 0.0) as monthly_spend
                FROM invoices
                WHERE month_str IS NOT NULL AND LENGTH(month_str) = 7
                GROUP BY month_str
                ORDER BY month_str ASC
                """
            )
            monthly_trend = [dict(row) for row in cursor.fetchall()]

            return {
                "total_invoices": totals["total_invoices"],
                "total_spend": round(totals["total_spend"], 2),
                "avg_amount": round(totals["avg_amount"], 2),
                "currency_totals": currency_totals,
                "top_vendors": top_vendors,
                "status_breakdown": status_breakdown,
                "monthly_trend": monthly_trend,
            }

    def get_work_queue(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch items needing human action, categorized by operational issue."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT i.*, 
                    (SELECT COUNT(*) FROM invoice_items WHERE invoice_id = i.id) as item_count
                FROM invoices i
                ORDER BY i.created_at DESC
                """
            )
            all_invoices = [dict(r) for r in cursor.fetchall()]

        queue_items: List[Dict[str, Any]] = []
        for inv in all_invoices:
            issues = []
            priority = "MEDIUM"

            # Check 1: Missing information
            missing = []
            if not inv.get("vendor_name") or inv.get("vendor_name") == "Unknown Vendor":
                missing.append("Vendor Name")
            if not inv.get("invoice_number") or inv.get("invoice_number") == "N/A":
                missing.append("Invoice Number")
            if not inv.get("invoice_date"):
                missing.append("Invoice Date")
            if float(inv.get("total_amount", 0.0) or 0.0) <= 0.0:
                missing.append("Total Amount")

            if missing:
                priority = "HIGH"
                issues.append({
                    "category": "MISSING_INFO",
                    "reason": f"Missing critical fields: {', '.join(missing)}",
                    "priority": "HIGH",
                })

            # Check 2: Validation discrepancy
            val_status = inv.get("validation_status", "")
            if val_status in ("DISCREPANCY", "NEEDS_REVIEW", "FAILED"):
                priority = "HIGH"
                issues.append({
                    "category": "VALIDATION_FAILED",
                    "reason": f"Validation status is '{val_status}' (mathematical imbalance or schema audit flag)",
                    "priority": "HIGH",
                })

            # Check 3: Potential duplicate
            if inv.get("is_duplicate") == 1 and inv.get("duplicate_decision") != "CONFIRMED_DUPLICATE" and inv.get("duplicate_decision") != "LEGITIMATE_SEPARATE":
                priority = "HIGH"
                issues.append({
                    "category": "POTENTIAL_DUPLICATE",
                    "reason": "Flagged as candidate duplicate; awaiting decision in Duplicate Review",
                    "priority": "HIGH",
                })

            # Check 4: Reconciliation required
            sub = float(inv.get("subtotal", 0.0) or 0.0)
            tax = float(inv.get("tax_amount", 0.0) or 0.0)
            shp = float(inv.get("shipping_amount", 0.0) or 0.0)
            dsc = float(inv.get("discount_amount", 0.0) or 0.0)
            tot = float(inv.get("total_amount", 0.0) or 0.0)
            calc_tot = round(sub + tax + shp - dsc, 2)
            if tot > 0 and sub > 0 and abs(tot - calc_tot) > 0.05:
                issues.append({
                    "category": "RECONCILIATION_REQUIRED",
                    "reason": f"Financial equation mismatch: Total {tot:.2f} != Subtotal+Tax+Ship-Disc ({calc_tot:.2f})",
                    "priority": "HIGH",
                })

            # Check 5: Under review general
            proc_status = inv.get("processing_status", "")
            if proc_status in ("EXTRACTED", "UNDER_REVIEW") and not issues:
                issues.append({
                    "category": "NEEDS_REVIEW",
                    "reason": "New extraction awaiting final operator review and approval",
                    "priority": "LOW",
                })

            for issue in issues:
                if not category or category == "ALL" or issue["category"] == category:
                    queue_items.append({
                        **inv,
                        "queue_category": issue["category"],
                        "issue_reason": issue["reason"],
                        "priority": issue["priority"],
                    })

        return queue_items

    def get_vendors_directory(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return aggregated vendor directory with spend totals by currency and invoice history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT
                    vendor_name,
                    currency,
                    COUNT(*) as invoice_count,
                    COALESCE(SUM(total_amount), 0.0) as total_spent,
                    MIN(COALESCE(invoice_date, created_at)) as first_invoice_date,
                    MAX(COALESCE(invoice_date, created_at)) as latest_invoice_date
                FROM invoices
                WHERE vendor_name IS NOT NULL AND vendor_name != ''
            """
            params: List[Any] = []
            if search:
                query += " AND vendor_name LIKE ?"
                params.append(f"%{search.strip()}%")

            query += " GROUP BY vendor_name, currency ORDER BY total_spent DESC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

        # Aggregate across currencies per vendor
        vendors_map: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            v_name = row["vendor_name"]
            if v_name not in vendors_map:
                vendors_map[v_name] = {
                    "vendor_name": v_name,
                    "total_invoices": 0,
                    "currencies": {},
                    "first_date": row["first_invoice_date"],
                    "latest_date": row["latest_invoice_date"],
                }
            vendors_map[v_name]["total_invoices"] += row["invoice_count"]
            vendors_map[v_name]["currencies"][row["currency"]] = round(row["total_spent"], 2)
            if row["first_invoice_date"] and (not vendors_map[v_name]["first_date"] or row["first_invoice_date"] < vendors_map[v_name]["first_date"]):
                vendors_map[v_name]["first_date"] = row["first_invoice_date"]
            if row["latest_invoice_date"] and (not vendors_map[v_name]["latest_date"] or row["latest_invoice_date"] > vendors_map[v_name]["latest_date"]):
                vendors_map[v_name]["latest_date"] = row["latest_invoice_date"]

        return list(vendors_map.values())

    def rename_vendor(self, old_name: str, new_name: str, changed_by: str = "Finance Operator") -> int:
        """Safely rename a vendor across all invoice records with audit trail."""
        if not old_name or not new_name or old_name == new_name:
            return 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM invoices WHERE vendor_name = ?", (old_name,))
            affected_ids = [row["id"] for row in cursor.fetchall()]

            cursor.execute("UPDATE invoices SET vendor_name = ?, updated_at = CURRENT_TIMESTAMP WHERE vendor_name = ?", (new_name, old_name))
            updated_count = cursor.rowcount

            for inv_id in affected_ids:
                cursor.execute(
                    """
                    INSERT INTO invoice_audit_trail (invoice_id, field_name, old_value, new_value, action)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (inv_id, "vendor_name", old_name, new_name, f"VENDOR_RENAME by {changed_by}"),
                )
            conn.commit()
            return updated_count

    def update_duplicate_decision(
        self,
        invoice_id: int,
        decision: str,
        notes: Optional[str] = None,
        changed_by: str = "Finance Operator",
    ) -> bool:
        """Record duplicate review decision ('CONFIRMED_DUPLICATE' or 'LEGITIMATE_SEPARATE')."""
        is_dup_val = 1 if decision == "CONFIRMED_DUPLICATE" else 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE invoices SET
                    duplicate_decision = ?,
                    is_duplicate = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (decision, is_dup_val, invoice_id),
            )
            cursor.execute(
                """
                INSERT INTO invoice_audit_trail (invoice_id, field_name, old_value, new_value, action)
                VALUES (?, ?, ?, ?, ?)
                """,
                (invoice_id, "duplicate_decision", None, f"{decision}: {notes or 'No notes'}", f"DUPLICATE_REVIEW by {changed_by}"),
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_reconciliation_status(
        self,
        invoice_id: int,
        status: str,
        notes: Optional[str] = None,
        changed_by: str = "Finance Operator",
    ) -> bool:
        """Update reconciliation status ('RECONCILED' or 'DISCREPANCY_FLAGGED')."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE invoices SET
                    reconciliation_status = ?,
                    reconciliation_notes = ?,
                    processing_status = CASE WHEN ? = 'RECONCILED' THEN 'RECONCILED' ELSE processing_status END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, notes, status, invoice_id),
            )
            cursor.execute(
                """
                INSERT INTO invoice_audit_trail (invoice_id, field_name, old_value, new_value, action)
                VALUES (?, ?, ?, ?, ?)
                """,
                (invoice_id, "reconciliation_status", None, f"{status} - {notes or ''}", f"RECONCILIATION by {changed_by}"),
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_processing_status(self, invoice_id: int, status: str) -> bool:
        """Update the workflow pipeline processing status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE invoices SET processing_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, invoice_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_pipeline_stage_counts(self) -> Dict[str, int]:
        """Return counts of invoices in each operational pipeline stage."""
        stages = ["IMPORTED", "EXTRACTED", "UNDER_REVIEW", "VALIDATED", "RECONCILED", "EXPORTED"]
        counts = {s: 0 for s in stages}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT processing_status, COUNT(*) as cnt FROM invoices GROUP BY processing_status")
            for row in cursor.fetchall():
                st = row["processing_status"]
                if st in counts:
                    counts[st] = row["cnt"]
                else:
                    counts["EXTRACTED"] += row["cnt"]
        return counts

    def get_all_audit_logs(
        self,
        limit: int = 150,
        action_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve system-wide audit history joined with invoice metadata."""
        query = """
            SELECT
                a.*,
                i.invoice_number,
                i.vendor_name,
                i.currency,
                i.total_amount
            FROM invoice_audit_trail a
            LEFT JOIN invoices i ON a.invoice_id = i.id
            WHERE 1=1
        """
        params: List[Any] = []
        if action_filter and action_filter != "ALL":
            query += " AND a.action LIKE ?"
            params.append(f"%{action_filter}%")

        query += " ORDER BY a.changed_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

    def get_recent_activity(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Return recent processing and modification activities for the overview desk."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    a.id as audit_id,
                    a.invoice_id,
                    a.field_name,
                    a.old_value,
                    a.new_value,
                    a.action,
                    a.changed_at,
                    i.vendor_name,
                    i.invoice_number,
                    i.total_amount,
                    i.currency
                FROM invoice_audit_trail a
                JOIN invoices i ON a.invoice_id = i.id
                ORDER BY a.changed_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_currency_spend_summary(self) -> List[Dict[str, Any]]:
        """Return distinct spend totals segregated strictly by currency (no multi-currency summing)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    currency,
                    COUNT(*) as invoice_count,
                    COALESCE(SUM(total_amount), 0.0) as total_amount,
                    COALESCE(AVG(total_amount), 0.0) as avg_amount,
                    COALESCE(SUM(tax_amount), 0.0) as total_tax
                FROM invoices
                GROUP BY currency
                ORDER BY total_amount DESC
                """
            )
            return [dict(r) for r in cursor.fetchall()]
