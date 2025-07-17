import json
import logging
import sys


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


class RailwayLogFormatter(logging.Formatter):
    """Output log record as JSON so Railway legge il livello corretto."""

    default_time_format = "%Y-%m-%dT%H:%M:%S"
    default_msec_format = "%s.%03d"

    def format(self, record: logging.LogRecord) -> str:  # noqa: N802
        log_record = {
            "time": self.formatTime(record, self.default_time_format),
            "level": record.levelname.lower(),
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger for Railway (stdout  JSON)."""
    root = logging.getLogger()
    root.setLevel(level)

    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)  # stdout ≠ error in Railway
    handler.setFormatter(RailwayLogFormatter())
    root.addHandler(handler)
