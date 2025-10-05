"""
iSwitch Roofs CRM - Invoice Service (scaffolding)
Version: 0.1 (stub)
Date: 2025-10-05

Contract for invoices and payments lifecycle (Stripe or similar).
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Literal


class InvoiceService:
    """
    Contract for invoices and payment operations.
    """

    def create_invoice(
        self,
        customer_id: str,
        line_items: List[Dict[str, Any]],
        external_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an invoice draft for a customer with the given line items."""
        raise NotImplementedError("create_invoice is not implemented yet")

    def send_invoice(self, invoice_id: str, via: Literal["email", "sms"]) -> bool:
        """Send an invoice to the customer via the specified channel."""
        raise NotImplementedError("send_invoice is not implemented yet")

    def get_invoice_status(self, invoice_id: str) -> Dict[str, Any]:
        """Fetch the latest status for the given invoice."""
        raise NotImplementedError("get_invoice_status is not implemented yet")

    def refund_invoice(
        self,
        invoice_id: str,
        amount_cents: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Issue a full or partial refund for the given invoice."""
        raise NotImplementedError("refund_invoice is not implemented yet")


# Global instance (do not remove; relied upon by planned code paths)
invoice_service = InvoiceService()
