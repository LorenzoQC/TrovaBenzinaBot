"""
Business logic for analysing fuel prices and rendering
a human-friendly HTML snippet.
"""
from typing import Dict, List, Tuple
from urllib.parse import quote_plus


def analyse(results: List[Dict], fid: int) -> Tuple[Tuple[Dict, float], float]:
    """
    Return (cheapest_station, cheapest_price) and the average price
    for fuel *fid* inside *results* (list of MISE API station dicts).
    """
    prices = [f["price"] for r in results for f in r["fuels"] if f["fuelId"] == fid]
    avg = sum(prices) / len(prices) if prices else 0
    station = results[0] if results else {}
    price = next((f["price"] for f in station.get("fuels", []) if f.get("fuelId") == fid), 0)
    return (station, price), avg


def fmt(station: Dict, price: float, avg: float, fuel: str) -> str:
    """Return an HTML snippet summarising *station* vs average *avg*."""
    pct = int(round((avg - price) / avg * 100)) if avg else 0
    lat = station.get("location", {}).get("lat")
    lng = station.get("location", {}).get("lng")
    dest = f"{lat},{lng}" if lat and lng else ""
    link = f"https://www.google.com/maps/dir/?api=1&destination={quote_plus(dest)}"

    saving = (
        f"<b>Savings:</b> {pct}% vs avg ({avg:.3f} €/L)"
        if pct
        else f"<b>Savings:</b> in line with avg ({avg:.3f} €/L)"
    )
    return "\n".join(
        [
            f"<b>Brand:</b> {station.get('brand', '')}",
            f"<b>Name:</b> {station.get('name', '')}",
            f"<b>Address:</b> {station.get('address', '')}",
            f"<b>{fuel} price:</b> {price:.3f} €/L",
            saving,
            f"<b><a href='{link}'>Let’s go!</a></b>",
        ]
    )
