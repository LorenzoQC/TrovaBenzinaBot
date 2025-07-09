def analyse(results, fid: int):
    """Return cheapest station and average price."""
    prices = [f["price"] for r in results for f in r["fuels"] if f["fuelId"] == fid]
    avg = sum(prices) / len(prices) if prices else 0
    station = results[0] if results else {}
    price = next((f["price"] for f in station.get("fuels", []) if f.get("fuelId") == fid), 0)
    return (station, price), avg


def fmt(station, price, avg, fuel):
    """Generate HTML overview of station info."""
    pct = int(round((avg - price) / avg * 100)) if avg else 0
    lat = station.get('location', {}).get('lat')
    lng = station.get('location', {}).get('lng')
    dest = f"{lat},{lng}" if lat and lng else ""
    link = f"https://www.google.com/maps/dir/?api=1&destination={dest}"
    save = (f"<b>Risparmio:</b> {pct}% vs avg ({avg:.3f} €/L)" if pct
            else f"<b>Risparmio:</b> in line with avg ({avg:.3f} €/L)")
    return "\n".join([
        f"<b>Brand:</b> {station.get('brand', '')}",
        f"<b>Distributore:</b> {station.get('name', '')}",
        f"<b>Indirizzo:</b> {station.get('address', '')}",
        f"<b>Costo {fuel}:</b> {price} €/L", save,
        f"<b><a href='{link}'>Andiamo!</a></b>",
    ])
