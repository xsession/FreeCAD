"""Dolibarr ERP integration adapter.

Syncs harness BOM data to a Dolibarr instance via its REST API.  Supports:

  * Push BOM line-items as Dolibarr products
  * Create / update BOMs linking those products
  * Query stock levels per component
  * Create supplier purchase orders from shortage lists
  * Pull supplier pricing back into the library
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .library import ComponentLibrary
from .model import ElectricalProjectModel
from .reports import ReportService

log = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────


@dataclass
class DolibarrConfig:
    base_url: str = "http://localhost"
    api_key: str = ""
    timeout_s: int = 30
    entity_id: str = ""  # multi-company support


# ── Low-level HTTP helpers ───────────────────────────────────────


def _headers(cfg: DolibarrConfig) -> Dict[str, str]:
    h: Dict[str, str] = {
        "DOLAPIKEY": cfg.api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if cfg.entity_id:
        h["DOLAPIENTITY"] = cfg.entity_id
    return h


def _request(
    method: str,
    url: str,
    cfg: DolibarrConfig,
    *,
    body: Optional[dict] = None,
) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method, headers=_headers(cfg),
    )
    with urllib.request.urlopen(req, timeout=cfg.timeout_s) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else {}


def _get(url: str, cfg: DolibarrConfig) -> Any:
    return _request("GET", url, cfg)


def _post(url: str, cfg: DolibarrConfig, body: dict) -> Any:
    return _request("POST", url, cfg, body=body)


def _put(url: str, cfg: DolibarrConfig, body: dict) -> Any:
    return _request("PUT", url, cfg, body=body)


# ── Product helpers ──────────────────────────────────────────────


def _product_ref(category: str, part_id: str) -> str:
    """Build a deterministic Dolibarr product ref from harness BOM data."""
    safe = f"EH-{category}-{part_id}"
    return safe[:48].replace("/", "-").replace(" ", "_")


def _find_product(cfg: DolibarrConfig, ref: str) -> Optional[dict]:
    """Search for an existing Dolibarr product by reference."""
    url = (
        f"{cfg.base_url}/api/index.php/products"
        f"?sqlfilters=(t.ref%3A%3D%3A'{ref}')&limit=1"
    )
    try:
        result = _get(url, cfg)
        if isinstance(result, list) and result:
            return result[0]
    except (urllib.error.URLError, OSError):
        pass
    return None


def _ensure_product(
    cfg: DolibarrConfig,
    ref: str,
    label: str,
    description: str,
    *,
    price: float = 0.0,
) -> int:
    """Get-or-create a product, returning the Dolibarr product id."""
    existing = _find_product(cfg, ref)
    if existing:
        return int(existing.get("id", existing.get("rowid", 0)))

    payload = {
        "ref": ref,
        "label": label,
        "description": description,
        "type": 0,  # product (not service)
        "status": 1,
        "status_buy": 1,
    }
    if price:
        payload["price"] = price
        payload["price_base_type"] = "HT"
    result = _post(f"{cfg.base_url}/api/index.php/products", cfg, payload)
    if isinstance(result, (int, float)):
        return int(result)
    if isinstance(result, dict):
        return int(result.get("id", result.get("rowid", 0)))
    return 0


# ── BOM sync ─────────────────────────────────────────────────────


def push_bom(
    cfg: DolibarrConfig,
    model: ElectricalProjectModel,
    assembly_name: str = "Electrical Harness Assembly",
) -> Dict[str, Any]:
    """Push the harness BOM to Dolibarr.

    1. Ensure each BOM line-item exists as a Dolibarr product.
    2. Create a parent assembly product.
    3. Create a Dolibarr BOM linking parent → children.

    Returns ``{"assembly_id": int, "bom_id": int, "line_count": int}``.
    """
    report = ReportService()
    bom_rows = report.bom(model)

    # Ensure each component-product exists
    child_products: List[Dict[str, Any]] = []
    for row in bom_rows:
        ref = _product_ref(row["category"], row["part_id"])
        label = row.get("description", row["part_id"])
        pid = _ensure_product(cfg, ref, label, label)
        child_products.append({
            "product_id": pid,
            "ref": ref,
            "qty": int(row.get("quantity", 1)),
            "description": label,
        })

    # Ensure assembly product
    asm_ref = _product_ref("Assembly", assembly_name)
    asm_id = _ensure_product(cfg, asm_ref, assembly_name, assembly_name)

    # Create BOM
    bom_payload = {
        "label": assembly_name,
        "fk_product": asm_id,
    }
    bom_result: Any = {}
    bom_id = 0
    try:
        bom_result = _post(f"{cfg.base_url}/api/index.php/boms", cfg, bom_payload)
        if isinstance(bom_result, (int, float)):
            bom_id = int(bom_result)
        elif isinstance(bom_result, dict):
            bom_id = int(bom_result.get("id", bom_result.get("rowid", 0)))
    except (urllib.error.URLError, OSError) as exc:
        log.warning("BOM creation failed (endpoint may not exist): %s", exc)

    # Add BOM lines
    line_count = 0
    if bom_id:
        for idx, child in enumerate(child_products, 1):
            line_payload = {
                "fk_product": child["product_id"],
                "qty": child["qty"],
                "position": idx,
                "description": child["description"],
            }
            try:
                _post(
                    f"{cfg.base_url}/api/index.php/boms/{bom_id}/lines",
                    cfg,
                    line_payload,
                )
                line_count += 1
            except (urllib.error.URLError, OSError) as exc:
                log.warning("BOM line %d failed: %s", idx, exc)

    return {
        "assembly_id": asm_id,
        "bom_id": bom_id,
        "line_count": line_count,
    }


# ── Stock queries ────────────────────────────────────────────────


def query_stock(
    cfg: DolibarrConfig,
    model: ElectricalProjectModel,
) -> List[Dict[str, Any]]:
    """Return stock levels for each BOM item.

    Each entry: ``{ ref, label, required, in_stock, shortage }``.
    """
    report = ReportService()
    bom_rows = report.bom(model)
    results: List[Dict[str, Any]] = []

    for row in bom_rows:
        ref = _product_ref(row["category"], row["part_id"])
        required = int(row.get("quantity", 1))
        product = _find_product(cfg, ref)
        in_stock = 0

        if product:
            pid = product.get("id", product.get("rowid"))
            try:
                stock_data = _get(
                    f"{cfg.base_url}/api/index.php/products/{pid}/stock",
                    cfg,
                )
                if isinstance(stock_data, list):
                    in_stock = sum(
                        int(s.get("qty", s.get("qty_real", 0)))
                        for s in stock_data
                    )
            except (urllib.error.URLError, OSError):
                pass

        results.append({
            "ref": ref,
            "label": row.get("description", ""),
            "required": required,
            "in_stock": in_stock,
            "shortage": max(0, required - in_stock),
        })

    return results


# ── Purchase order creation ──────────────────────────────────────


def create_purchase_order(
    cfg: DolibarrConfig,
    supplier_id: int,
    shortages: List[Dict[str, Any]],
    *,
    note: str = "",
) -> int:
    """Create a Dolibarr purchase order for shortage items.

    *shortages*: entries from ``query_stock`` with shortage > 0.
    Returns the Dolibarr order id.
    """
    items = [s for s in shortages if s.get("shortage", 0) > 0]
    if not items:
        return 0

    order_payload: Dict[str, Any] = {
        "socid": supplier_id,
        "note_private": note or "Auto-generated from FreeCAD ElectricalHarness",
    }
    try:
        result = _post(
            f"{cfg.base_url}/api/index.php/supplier_orders",
            cfg,
            order_payload,
        )
        order_id = 0
        if isinstance(result, (int, float)):
            order_id = int(result)
        elif isinstance(result, dict):
            order_id = int(result.get("id", result.get("rowid", 0)))
    except (urllib.error.URLError, OSError) as exc:
        log.warning("Supplier order creation failed: %s", exc)
        return 0

    if not order_id:
        return 0

    for idx, item in enumerate(items, 1):
        product = _find_product(cfg, item["ref"])
        if not product:
            continue
        pid = product.get("id", product.get("rowid"))
        line_payload = {
            "fk_product": pid,
            "desc": item.get("label", ""),
            "qty": item["shortage"],
            "subprice": 0,
            "tva_tx": 0,
            "position": idx,
        }
        try:
            _post(
                f"{cfg.base_url}/api/index.php/supplier_orders/{order_id}/lines",
                cfg,
                line_payload,
            )
        except (urllib.error.URLError, OSError) as exc:
            log.warning("Order line %d failed: %s", idx, exc)

    return order_id


# ── Supplier pricing → library ───────────────────────────────────


def pull_supplier_pricing(
    cfg: DolibarrConfig,
    library: ComponentLibrary,
) -> int:
    """Enrich library entries with supplier pricing from Dolibarr.

    Searches Dolibarr products matching library part numbers and stores
    price info in the entry's attributes dict.  Returns count updated.
    """
    count = 0
    for entry in library.all_entries():
        if not entry.part_number:
            continue
        url = (
            f"{cfg.base_url}/api/index.php/products"
            f"?sqlfilters=(t.ref%3Alike%3A'%25{entry.part_number}%25')&limit=1"
        )
        try:
            result = _get(url, cfg)
            if isinstance(result, list) and result:
                product = result[0]
                entry.attributes["dolibarr_id"] = str(
                    product.get("id", product.get("rowid", ""))
                )
                price = product.get("price", product.get("price_ttc", ""))
                if price:
                    entry.attributes["unit_price"] = str(price)
                count += 1
        except (urllib.error.URLError, OSError):
            continue
    return count


# ── High-level adapter ───────────────────────────────────────────


class DolibarrAdapter:
    """High-level adapter for Dolibarr ERP integration."""

    def __init__(self, cfg: DolibarrConfig):
        self.cfg = cfg

    def push_bom(
        self,
        model: ElectricalProjectModel,
        assembly_name: str = "Electrical Harness Assembly",
    ) -> Dict[str, Any]:
        return push_bom(self.cfg, model, assembly_name)

    def query_stock(
        self, model: ElectricalProjectModel,
    ) -> List[Dict[str, Any]]:
        return query_stock(self.cfg, model)

    def create_purchase_order(
        self,
        supplier_id: int,
        shortages: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> int:
        return create_purchase_order(self.cfg, supplier_id, shortages, **kwargs)

    def pull_pricing(self, library: ComponentLibrary) -> int:
        return pull_supplier_pricing(self.cfg, library)

    def test_connection(self) -> bool:
        """Verify the Dolibarr API is reachable and the key is valid."""
        try:
            _get(f"{self.cfg.base_url}/api/index.php/status", self.cfg)
            return True
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            return False

    def list_suppliers(self) -> List[Dict[str, Any]]:
        """Return all third parties marked as suppliers."""
        url = f"{self.cfg.base_url}/api/index.php/thirdparties?mode=2&limit=200"
        try:
            result = _get(url, self.cfg)
            return result if isinstance(result, list) else []
        except (urllib.error.URLError, OSError):
            return []
