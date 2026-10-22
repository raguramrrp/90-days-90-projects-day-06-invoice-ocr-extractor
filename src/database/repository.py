"""Database Repository for Invoices and Invoice Items.

Provides thread-safe CRUD operations, search filters, and aggregate analytics
using standard library sqlite3 with foreign key enforcement.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import config
from src.database.models import CREATE_INDEXES, CREATE_INVOICE_ITEMS_TABLE, CREATE_INVOICES_TABLE


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
        """Create tables and performance indices if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(CREATE_INVOICES_TABLE)
            cursor.execute(CREATE_INVOICE_ITEMS_TABLE)
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
                    filename, vendor_name, invoice_number, invoice_date, due_date,
                    currency, subtotal, tax_amount, shipping_amount, discount_amount,
                    total_amount, payment_terms, po_number, overall_confidence,
                    validation_status, raw_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    filename or invoice_data.get("filename"),
                    invoice_data.get("vendor_name", "Unknown Vendor"),
                    invoice_data.get("invoice_number", "N/A"),
                    invoice_data.get("invoice_date"),
                    invoice_data.get("due_date"),
                    invoice_data.get("currency", "USD"),
                    float(invoice_data.get("subtotal", 0.0) or 0.0),
                    float(invoice_data.get("tax_amount", 0.0) or 0.0),
                    float(invoice_data.get("shipping_amount", 0.0) or 0.0),
                    float(invoice_data.get("discount_amount", 0.0) or 0.0),
                    float(invoice_data.get("total_amount", 0.0) or 0.0),
                    invoice_data.get("payment_terms"),
                    invoice_data.get("po_number"),
                    float(invoice_data.get("overall_confidence", 0.0) or 0.0),
                    invoice_data.get("validation_status", "PENDING"),
                    invoice_data.get("raw_text", ""),
                ),
            )
            invoice_id = cursor.lastrowid

            if items_list:
                for item in items_list:
                    cursor.execute(
                        """
                        INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, amount)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            invoice_id,
                            item.get("description", "Item"),
                            float(item.get("quantity", 1.0) or 1.0),
                            float(item.get("unit_price", 0.0) or 0.0),
                            float(item.get("amount", 0.0) or 0.0),
                        ),
                    )

            conn.commit()
            return int(invoice_id)

    def get_invoices(
        self,
        search_query: Optional[str] = None,
        vendor: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve invoices matching optional search queries and filters."""
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

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a specific invoice and all attached line items."""
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

            return inv_dict

    def update_invoice(
        self,
        invoice_id: int,
        invoice_data: Dict[str, Any],
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Update an existing invoice record and re-sync its line items."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE invoices SET
                    vendor_name = ?,
                    invoice_number = ?,
                    invoice_date = ?,
                    due_date = ?,
                    currency = ?,
                    subtotal = ?,
                    tax_amount = ?,
                    shipping_amount = ?,
                    discount_amount = ?,
                    total_amount = ?,
                    payment_terms = ?,
                    po_number = ?,
                    validation_status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    invoice_data.get("vendor_name", "Unknown Vendor"),
                    invoice_data.get("invoice_number", "N/A"),
                    invoice_data.get("invoice_date"),
                    invoice_data.get("due_date"),
                    invoice_data.get("currency", "USD"),
                    float(invoice_data.get("subtotal", 0.0) or 0.0),
                    float(invoice_data.get("tax_amount", 0.0) or 0.0),
                    float(invoice_data.get("shipping_amount", 0.0) or 0.0),
                    float(invoice_data.get("discount_amount", 0.0) or 0.0),
                    float(invoice_data.get("total_amount", 0.0) or 0.0),
                    invoice_data.get("payment_terms"),
                    invoice_data.get("po_number"),
                    invoice_data.get("validation_status", "VALIDATED"),
                    invoice_id,
                ),
            )

            if items is not None:
                # Replace line items
                cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
                for item in items:
                    cursor.execute(
                        """
                        INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, amount)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            invoice_id,
                            item.get("description", "Item"),
                            float(item.get("quantity", 1.0) or 1.0),
                            float(item.get("unit_price", 0.0) or 0.0),
                            float(item.get("amount", 0.0) or 0.0),
                        ),
                    )

            conn.commit()
            return cursor.rowcount > 0

    def delete_invoice(self, invoice_id: int) -> bool:
        """Delete an invoice record (cascading deletes line items)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Aggregate summary metrics for executive dashboards."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total counts & sums
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

            # Top vendors
            cursor.execute(
                """
                SELECT
                    vendor_name,
                    COUNT(*) as invoice_count,
                    COALESCE(SUM(total_amount), 0.0) as total_spent
                FROM invoices
                GROUP BY vendor_name
                ORDER BY total_spent DESC
                LIMIT 5
                """
            )
            top_vendors = [dict(row) for row in cursor.fetchall()]

            # Validation status breakdown
            cursor.execute(
                """
                SELECT validation_status, COUNT(*) as count
                FROM invoices
                GROUP BY validation_status
                """
            )
            status_breakdown = {row["validation_status"]: row["count"] for row in cursor.fetchall()}

            return {
                "total_invoices": totals["total_invoices"],
                "total_spend": round(totals["total_spend"], 2),
                "avg_amount": round(totals["avg_amount"], 2),
                "top_vendors": top_vendors,
                "status_breakdown": status_breakdown,
            }
