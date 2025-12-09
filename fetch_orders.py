import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any

API_URL = "https://api.baselinker.com/connector.php"

def to_timestamp(date_str: str) -> int:
    """Convert 'YYYY-MM-DD' to a Unix timestamp at 00:00:00 that day."""
    dt = datetime.strptime(date_str + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp())

def fetch_orders(date_str: Optional[str] = None, timestamp: Optional[int] = None, token: str = "") -> Dict[str, Any]:
    """
    Fetch orders from BaseLinker API.
    Provide either date_str (YYYY-MM-DD) or timestamp (int).
    Returns parsed JSON on success, raises RuntimeError on failure.
    """
    if timestamp is None:
        if not date_str:
            raise ValueError("Either date_str or timestamp must be provided")
        timestamp = to_timestamp(date_str)

    headers = {
        "X-BLToken": token,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "method": "getOrders",
        "parameters": f'{{"date_from": {timestamp}}}',
    }

    resp = requests.post(API_URL, headers=headers, data=data)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to fetch orders: {resp.status_code} - {resp.text}")
    return resp.json()

def save_orders_to_file(orders: Dict[str, Any], filename: str = "orders.json") -> None:
    """Save orders dict to a JSON file (UTF-8)."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=4, ensure_ascii=False)


