"""Week 3: validation (BR-19) and the rules not yet covered by test_rules.py."""
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path

from ride import engine as E
from ride.config import Rules
from ride.loaders import load_drivers, load_rate_card, load_sessions, load_slots
from ride.processor import Processor
from ride.validation import RideError, dec, whole, stamp

R = Rules()
DATA = str(Path(__file__).resolve().parent.parent / "data")
REQ = "REQUEST|T1|2026-10-12 09:05:00|RDR-1|MINI|ZN-1|5|15|DRV-01:1.0"


def proc():
    return Processor(R, load_rate_card(DATA), load_drivers(DATA), load_slots(DATA), load_sessions(DATA))


def feed(p, *lines):
    p.run([(i + 1, l.split("|")[0], l.split("|")[1:]) for i, l in enumerate(lines)])
    return [e["message"] for e in p.errors]


def one_error(*lines):
    errs = feed(proc(), *lines)
    assert len(errs) == 1, errs
    return errs[0]


# ---- BR-01 demand/supply slots ----
def test_slot_floor_to_15_minutes():                                # BR-01
    assert E.slot_start(datetime(2026, 10, 12, 18, 33, 40)) == datetime(2026, 10, 12, 18, 30)


def test_missing_slot_is_rejected_with_message():                   # BR-01, BR-19
    msg = one_error("REQUEST|T1|2030-01-01 09:05:00|R|MINI|ZN-1|5|15|DRV-01:1.0")
    assert "no demand/supply data" in msg


# ---- BR-04 peak and BR-15 incentive ----
def test_peak_window_by_start_time():                               # BR-04
    assert E.is_peak(R, datetime(2026, 10, 12, 8, 0)) and E.is_peak(R, datetime(2026, 10, 12, 9, 50))
    assert not E.is_peak(R, datetime(2026, 10, 12, 10, 0))
    assert E.is_peak(R, datetime(2026, 10, 12, 17, 0)) and not E.is_peak(R, datetime(2026, 10, 12, 20, 0))


def test_incentive_slabs_and_eligibility():                         # BR-15
    assert E.incentive(R, D("20"), True) == D("700.00")
    assert E.incentive(R, D("19.5"), True) == D("300.00")     # non-cumulative: 300, not 300 + 700
    assert E.incentive(R, D("12"), True) == D("300.00")
    assert E.incentive(R, D("11.5"), True) == D("0.00")
    assert E.incentive(R, D("20"), False) == D("0.00")


# ---- BR-14 commission and BR-17 rounding ----
def test_commission_is_percent_of_fare_and_night_only():            # BR-14
    p = proc()
    feed(p, REQ, "ACCEPTED|T1|2026-10-12 09:06:00", "ARRIVED|T1|2026-10-12 09:10:00",
         "START|T1|2026-10-12 09:11:00", "END|T1|2026-10-12 09:31:00|6.0|0|40")
    b = p.trips["T1"]["bill"]
    assert b.commission == E.q2((b.charged + b.night) * R.commission_pct / 100)
    assert b.payout == b.charged + b.night - b.commission + b.pickup_wait + b.mid_wait + b.toll


def test_rounding_is_half_up_to_paisa_and_rupee():                  # BR-17
    assert E.q2(D("0.005")) == D("0.01")
    assert E.q2(D("0.004")) == D("0.00")
    assert E.rupee(D("10.5")) == D("11")


# ---- BR-19 validation: one test per bad-input case ----
def test_field_validators():                                        # BR-19
    for call in (lambda: dec("km", "abc"), lambda: dec("km", "-1", 0), lambda: dec("km", "NaN"),
                 lambda: whole("min", "2.5"), lambda: whole("stars", "9", 1, 5),
                 lambda: stamp("time", "not a time")):
        try:
            call()
        except RideError:
            continue
        raise AssertionError("expected RideError")


def test_unknown_command():                                         # BR-19
    assert "unknown command" in one_error("HONK|T1|x")


def test_wrong_field_count():                                       # BR-19
    assert "needs 8 fields but got 2" in one_error("REQUEST|T1|2026-10-12 09:05:00")


def test_unknown_category_driver_and_trip():                        # BR-19
    assert "unknown category" in one_error(REQ.replace("MINI", "JET"))
    assert "unknown driver" in one_error(REQ.replace("DRV-01", "DRV-99"))
    assert "unknown trip" in one_error("ACCEPTED|NOPE|2026-10-12 09:06:00")


def test_negative_and_non_numeric_values():                         # BR-19
    assert "at least 0" in one_error(REQ.replace("|5|15|", "|-5|15|"))
    assert "not a number" in one_error(REQ.replace("|5|15|", "|five|15|"))
    assert "not a whole number" in one_error(REQ.replace("|5|15|", "|5|15.5|"))


def test_bad_timestamp():                                           # BR-19
    assert "not a valid timestamp" in one_error(REQ.replace("2026-10-12 09:05:00", "yesterday"))


def test_duplicate_trip_id():                                       # BR-19
    errs = feed(proc(), REQ, REQ)
    assert errs == ["duplicate trip id T1"]


def test_events_out_of_order_are_rejected():                        # BR-19
    errs = feed(proc(), REQ, "START|T1|2026-10-12 09:20:00", "END|T1|2026-10-12 09:40:00|5|0|0")
    assert "cannot start while trip is REQUESTED" in errs[0]
    assert "cannot end while trip is REQUESTED" in errs[1]


def test_time_going_backwards_is_rejected():                        # BR-19
    errs = feed(proc(), REQ, "ACCEPTED|T1|2026-10-12 09:00:00")
    assert "is before request time" in errs[0]


def test_cannot_cancel_or_rate_wrongly():                           # BR-19
    errs = feed(proc(), REQ, "RATE|T1|5", "CANCEL_DRIVER|T1|2026-10-12 09:06:00")
    assert "cannot rate while trip is REQUESTED" in errs[0]
    assert "cannot cancel (driver) while trip is REQUESTED" in errs[1]


def test_rating_out_of_range():                                     # BR-19
    lines = [REQ, "ACCEPTED|T1|2026-10-12 09:06:00", "ARRIVED|T1|2026-10-12 09:08:00",
             "START|T1|2026-10-12 09:09:00", "END|T1|2026-10-12 09:30:00|5|0|0", "RATE|T1|7"]
    assert "must be at most 5" in feed(proc(), *lines)[0]


def test_bad_command_does_not_stop_the_run():                       # BR-19
    p = proc()
    feed(p, "HONK|x", REQ, "ACCEPTED|T1|2026-10-12 09:06:00")
    assert p.trips["T1"]["status"] == "ACCEPTED" and len(p.errors) == 1


def test_unknown_driver_in_statements():                            # BR-19
    assert "unknown driver" in one_error("PRINT_DAILY|DRV-99|2026-10-12")
    assert "unknown driver" in one_error("PRINT_WEEKLY|DRV-99|2026-10-12")


# ---- new tests for rules the brief pins down ----
def test_upfront_protection_three_cases():                          # BR-08
    q = D("120.00")
    assert E.protect(R, q, D("100.00")) == D("100.00")      # lower: pays actual
    assert E.protect(R, q, D("144.00")) == q                # exactly +20%: pays quote
    assert E.protect(R, q, D("150.00")) == D("126.00")      # beyond: actual - 20% of quote


def test_mid_trip_wait_charged_only_beyond_five_minutes():          # BR-07
    card = load_rate_card(DATA)["MINI"]
    t0, t1, t2 = datetime(2026, 10, 12, 10, 0), datetime(2026, 10, 12, 10, 1), datetime(2026, 10, 12, 10, 30)
    q = D("100.00")
    assert E.bill(card, R, D("1.0"), q, t0, t1, t2, D("5"), D("5"), D("0")).mid_wait == D("0.00")
    assert E.bill(card, R, D("1.0"), q, t0, t1, t2, D("5"), D("8"), D("0")).mid_wait == D("6.00")


def test_second_nearest_with_score_90_gets_first_offer():           # BR-10
    sc = {"A": 80, "B": 90, "C": 95}
    assert E.offer_order(R, [("A", D("0.6")), ("B", D("0.9")), ("C", D("2.0"))], sc) == ["B", "A", "C"]
    assert E.offer_order(R, [("A", D("0.6")), ("C", D("0.9"))], {"A": 95, "C": 99}) == ["A", "C"]
    assert E.offer_order(R, [("A", D("0.6")), ("B", D("3.4"))], sc) == ["A"]       # beyond 3 km
    assert E.offer_order(R, [("A", D("0.79")), ("B", D("1.99"))], sc) == ["A", "B"]  # too far behind to jump (TRP-0078)


def test_sedan_cancel_fee_is_higher():                              # BR-12
    t = datetime(2026, 10, 12, 13, 20, 0)
    late = datetime(2026, 10, 12, 13, 25, 0)
    assert E.cancel_fee(R, "SEDAN", t, late, 4) == D("50.00")
    assert E.cancel_fee(R, "BIKE", t, late, 4) == D("30.00")
    assert E.cancel_fee(R, "SEDAN", t, late, 11) == D("0.00")         # driver > 10 min away
