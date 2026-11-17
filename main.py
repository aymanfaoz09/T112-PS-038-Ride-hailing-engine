"""python main.py [data_dir] [out_dir]  ->  trip_invoices.csv, driver_daily.csv, driver_weekly.csv"""
import csv
import sys
from pathlib import Path

from ride.config import Rules
from ride.loaders import (load_commands, load_drivers, load_rate_card, load_sessions, load_slots)
from ride.processor import Processor

INV = ["trip_id", "status", "driver_id", "category", "surge_multiplier", "quote", "actual_fare",
       "fare_charged", "night_charge", "pickup_wait_charge", "mid_trip_wait_charge", "toll",
       "cancellation_fee", "gst", "rider_total", "commission", "driver_payout", "rule_ids"]
DAILY = ["driver_id", "date", "trips_completed", "incentive_trip_count", "acceptance_score_eod",
         "incentive_eligible", "trip_earnings", "cancellation_income", "incentive", "daily_net"]
WEEKLY = ["driver_id", "week_start", "online_minutes", "acceptance_pct", "weekly_net_before_topup",
          "guarantee_topup", "weekly_net"]


def write(path, cols, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def run(data="data", out="out"):
    p = Processor(Rules(), load_rate_card(data), load_drivers(data), load_slots(data), load_sessions(data))
    p.run(load_commands(data))
    Path(out).mkdir(exist_ok=True)
    write(Path(out) / "trip_invoices.csv", INV, p.out_invoices)
    write(Path(out) / "driver_daily.csv", DAILY, p.out_daily)
    write(Path(out) / "driver_weekly.csv", WEEKLY, p.out_weekly)
    write(Path(out) / "errors.csv", ["line", "command", "message"], p.errors)
    return p


if __name__ == "__main__":
    a = sys.argv[1:]
    p = run(*a)
    print(f"{len(p.out_invoices)} invoices, {len(p.out_daily)} daily rows, {len(p.out_weekly)} weekly rows, {len(p.errors)} rejected commands")
