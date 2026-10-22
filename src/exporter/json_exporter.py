"""JSON Exporter for Extracted Invoice Data.

Serializes single or batch invoice records into clean, well-indented JSON structures.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Union


def export_to_json(data: Union[Dict[str, Any], List[Dict[str, Any]]], indent: int = 2) -> str:
    """Serialize dictionary or list of invoice records to structured JSON string."""
    # Ensure non-serializable objects (such as sets or custom types) are converted
    def default_serializer(obj: Any) -> Any:
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)

    return json.dumps(data, indent=indent, default=default_serializer, ensure_ascii=False)
