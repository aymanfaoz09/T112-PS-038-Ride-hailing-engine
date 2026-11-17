"""Business-rule constants taken from the brief (PS-038). Money is Decimal.
Choices the brief leaves open are marked DECISION and listed in the decision log."""
from dataclasses import dataclass
from datetime import time
from decimal import Decimal as D


@dataclass(frozen=True)
class Card:
    base_fare: D
    base_km: D
    per_km: D
    per_min: D
    surge_cap: D


@dataclass(frozen=True)
class Rules:
    # BR-02 surge bands (min demand/supply ratio, inclusive -> multiplier), high to low.
    # Below 1.2 -> 1.0. DECISION: a ratio exactly on a boundary takes the higher band
    # (confirmed for 1.2 and 1.6 by the sample pack's edge cases).
    surge_bands: tuple = ((D("2.0"), D("2.0")), (D("1.6"), D("1.6")), (D("1.2"), D("1.3")))
    # BR-04 peak windows [from, to) judged by trip START time; peak trip counts 1.5
    peak_windows: tuple = ((time(8, 0), time(10, 0)), (time(17, 0), time(20, 0)))
    peak_weight: D = D("1.5")
    # BR-06 night window [23:00, 05:00) by pickup (START) time; +25% on the surged fare
    night_start: time = time(23, 0)
    night_end: time = time(5, 0)
    night_pct: D = D("25")
    # BR-08 upfront protection: within +20% -> rider pays quote; beyond -> actual - 20% of quote.
    # DECISION: the +20% test is made on paisa-rounded amounts.
    quote_cap_pct: D = D("120")
    protect_excess_pct: D = D("20")
    # BR-07 waiting (never surged): 3 free pickup minutes then Rs 1/min;
    # mid-trip stops beyond 5 minutes total at Rs 2/min (on the minutes beyond 5)
    free_wait_min: int = 3
    wait_rate: D = D("1.00")
    mid_wait_threshold: int = 5
    mid_wait_rate: D = D("2.00")
    # BR-14 platform keeps 20% of the fare excluding tolls and waiting; GST 5% on the fare
    # DECISION: "the fare" = fare charged after protection + night charge
    commission_pct: D = D("20")
    gst_pct: D = D("5")
    # BR-10 matching: nearest driver within 3 km; a score >= 90 second-nearest gets first offer
    radius_km: D = D("3.0")
    priority_score: int = 90
    # DECISION: the brief gives no distance limit for the jump. TRP-0038 (0.35 km gap) jumps and
    # TRP-0078 (1.20 km gap) does not, so the second nearest may jump if within 0.5 km of the nearest.
    priority_gap_km: D = D("0.5")
    # BR-12 rider cancellation: free within 2 min of acceptance (inclusive), or driver > 10 min away
    free_cancel_sec: int = 120
    far_eta_min: int = 10
    cancel_fee: D = D("30.00")
    cancel_fee_sedan: D = D("50.00")
    cancel_driver_pct: D = D("80")
    # BR-13 driver cancel: score -5; below 70 loses the day's incentive (70 exactly stays eligible)
    cancel_penalty: int = 5
    incentive_min_score: int = 70
    # BR-15 daily incentive, non-cumulative; only trips rated >= 4 count
    min_rating: int = 4
    incentive_slabs: tuple = ((D("20"), D("700")), (D("12"), D("300")))
    # BR-16 weekly guarantee: 60+ h online and acceptance >= 85% -> topped up to Rs 9,000 net
    guarantee_min_online: int = 3600
    guarantee_min_accept: D = D("85")
    guarantee_amount: D = D("9000.00")
