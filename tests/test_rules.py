import csv
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path

from main import run
from ride.config import Card, Rules
from ride import engine as E

R = Rules()
ROOT = Path(__file__).resolve().parent.parent
MINI = Card(D("50"), D("2"), D("12"), D("1.5"), D("2.0"))


def rows(name):
    with open(ROOT / "out" / name) as f:
        return list(csv.DictReader(f))


def setup_module(_):
    run(str(ROOT / "data"), str(ROOT / "out"))


def inv(trip):
    return next(r for r in rows("trip_invoices.csv") if r["trip_id"] == trip)


def test_surge_band_boundaries():                      # BR-02, EC-02
    assert E.surge_multiplier(R, MINI, 119, 100) == D("1.0")
    assert E.surge_multiplier(R, MINI, 60, 50) == D("1.3")     # exactly 1.2
    assert E.surge_multiplier(R, MINI, 80, 50) == D("1.6")     # exactly 1.6
    assert E.surge_multiplier(R, MINI, 110, 50) == D("2.0")


def test_surge_capped_by_category():                   # BR-02b
    bike = Card(D("20"), D("2"), D("6"), D("0"), D("1.5"))
    assert E.surge_multiplier(R, bike, 110, 50) == D("1.5")


def test_exactly_two_km_is_base_fare_only():           # BR-03, EC-01
    assert E.raw_fare(MINI, D("2.0"), D("11")) == D("66.50")
    assert inv("TRP-0034")["actual_fare"] == "66.50"


def test_night_boundary_at_pickup():                   # BR-06, EC-03
    assert E.is_night(R, datetime(2026, 10, 15, 23, 0, 0))
    assert not E.is_night(R, datetime(2026, 10, 16, 5, 0, 0))
    assert inv("TRP-0095")["night_charge"] != "0.00"
    assert inv("TRP-0097")["night_charge"] == "0.00"


def test_night_charge_is_on_the_surged_fare():         # BR-05
    card = MINI
    mult = D("1.6")
    q = E.quote(card, R, mult, D("8"), 20)
    b = E.bill(card, R, mult, q, datetime(2026, 10, 15, 22, 50), datetime(2026, 10, 15, 23, 0),
               datetime(2026, 10, 15, 23, 20), D("8"), D("0"), D("0"))
    assert b.night == E.q2(b.charged * R.night_pct / 100)


def test_waiting_and_toll_not_surged_or_commissioned():  # BR-07
    r = inv("TRP-0108")
    assert r["pickup_wait_charge"] == "4.00" and r["mid_trip_wait_charge"] == "6.00"
    assert r["toll"] == "35.00"
    base = D(r["fare_charged"]) + D(r["night_charge"])
    assert D(r["commission"]) == E.q2(base * R.commission_pct / 100)
    assert D(r["driver_payout"]) == base - D(r["commission"]) + D("4") + D("6") + D("35")


def test_actual_fare_capped_at_quote_plus_20pct():     # BR-08, EC-04
    a, b = inv("TRP-0027"), inv("TRP-0028")
    assert a["actual_fare"] == "144.03" and a["fare_charged"] == "120.03"   # beyond +20%: actual - 20% of quote
    assert b["actual_fare"] == "143.94" and b["fare_charged"] == "120.00"   # within +20%: pays the quote


def test_no_driver_within_radius_is_unmatched():       # BR-10
    r = inv("TRP-0143")
    assert r["status"] == "UNMATCHED" and r["driver_id"] == ""


def test_high_score_second_nearest_gets_first_offer_then_times_out():   # BR-10
    r = inv("TRP-0038")
    assert r["status"] == "COMPLETED" and r["driver_id"] == "DRV-13"


def test_rider_cancel_fee_and_split():                 # BR-12
    r = inv("TRP-0127")
    assert r["status"] == "CANCELLED_RIDER"
    assert (r["cancellation_fee"], r["driver_payout"], r["commission"]) == ("50.00", "40.00", "10.00")   # SEDAN Rs 50, 80% to driver


def test_cancel_at_exactly_two_minutes_is_free():      # BR-12, EC-05
    assert D(inv("TRP-0010")["cancellation_fee"]) == 0
    t = datetime(2026, 10, 12, 19, 12, 7)
    assert E.cancel_fee(R, "MINI", t, datetime(2026, 10, 12, 19, 14, 7), 10) == 0
    assert E.cancel_fee(R, "MINI", t, datetime(2026, 10, 12, 19, 14, 8), 10) == R.cancel_fee


def test_score_exactly_70_stays_eligible():            # BR-13, EC-06
    d = next(r for r in rows("driver_daily.csv") if r["driver_id"] == "DRV-06" and r["date"] == "2026-10-15")
    assert d["acceptance_score_eod"] == "70" and d["incentive_eligible"] == "true"


def test_weekly_guarantee_threshold():                 # BR-16, EC-08
    w = {r["driver_id"]: r for r in rows("driver_weekly.csv")}
    assert w["DRV-16"]["online_minutes"] == "3599" and w["DRV-16"]["guarantee_topup"] == "0.00"
    assert w["DRV-19"]["online_minutes"] == "3600" and D(w["DRV-19"]["guarantee_topup"]) > 0


def test_output_shapes():
    assert len(rows("trip_invoices.csv")) == 150
    assert len(rows("driver_daily.csv")) == 140
    assert len(rows("driver_weekly.csv")) == 20
