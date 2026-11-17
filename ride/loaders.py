import csv
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path

from .config import Card

FORMATS = ("%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M")


def ts(s):
    s = s.strip()
    for f in FORMATS:
        try:
            return datetime.strptime(s, f)
        except ValueError:
            pass
    raise ValueError(f"unrecognised timestamp {s!r}")


def _rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        first = f.readline()
        f.seek(0)
        delim = "\t" if "\t" in first else ","
        return list(csv.DictReader(f, delimiter=delim))


def load_rate_card(d):
    return {r["category"]: Card(D(r["base_fare"]), D(r["base_km"]), D(r["per_km"]),
                                D(r["per_min"]), D(r["surge_cap"]))
            for r in _rows(Path(d) / "rate_card.csv")}


def load_drivers(d):
    return {r["driver_id"]: {"category": r["category"], "score": int(r["acceptance_score_start"])}
            for r in _rows(Path(d) / "drivers.csv")}


def load_slots(d):
    return {(r["zone_id"], ts(r["slot_start"])): (int(r["demand"]), int(r["supply"]))
            for r in _rows(Path(d) / "demand_supply.csv")}


def load_sessions(d):
    out = {}
    for r in _rows(Path(d) / "driver_sessions.csv"):
        out.setdefault(r["driver_id"], []).append((ts(r["login_ts"]), ts(r["logout_ts"])))
    return out


def load_commands(d):
    """Returns (line_number, COMMAND, [fields]) so errors can point at the exact line."""
    files = sorted(Path(d).glob("commands*"))
    if not files:
        raise FileNotFoundError(f"no commands file found in {d}")
    cmds = []
    with open(files[0], encoding="utf-8-sig") as f:
        for n, line in enumerate(f, start=1):
            line = line.strip()
            if line and not line.startswith("#"):
                parts = [p.strip() for p in line.split("|")]
                cmds.append((n, parts[0].upper(), parts[1:]))
    return cmds
