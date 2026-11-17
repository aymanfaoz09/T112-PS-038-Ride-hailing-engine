"""Pure pricing and matching functions (no state)."""
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal as D, ROUND_CEILING, ROUND_HALF_UP
from fractions import Fraction


def q2(x):
    """BR-17: money is Decimal, rounded half-up to the paisa."""
    return D(x).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def rupee(x):
    return D(x).quantize(D("1"), rounding=ROUND_HALF_UP)


def minutes(td):
    return D(td.total_seconds()) / 60


def slot_start(t):
    return t.replace(minute=t.minute - t.minute % 15, second=0, microsecond=0)


def surge_multiplier(rules, card, demand, supply):
    """BR-02: band lower bound is inclusive; capped by the category (BR-02b)."""
    mult = D("1.0")
    if supply == 0:
        mult = rules.surge_bands[0][1]
    else:
        ratio = Fraction(demand, supply)
        for lo, m in rules.surge_bands:
            if ratio >= Fraction(lo):
                mult = m
                break
    return min(mult, card.surge_cap)


def raw_fare(card, km, ride_min):
    """BR-03: base fare covers base_km and is the minimum fare."""
    extra = max(D(0), km - card.base_km)
    return max(card.base_fare, card.base_fare + extra * card.per_km + ride_min * card.per_min)


def in_window(t, windows):
    return any(a <= t.time() < b for a, b in windows)


def is_night(rules, t):
    tt = t.time()
    return tt >= rules.night_start or tt < rules.night_end


def is_peak(rules, t):
    return in_window(t, rules.peak_windows)


def quote(card, rules, mult, est_km, est_min):
    return q2(raw_fare(card, est_km, D(est_min)) * mult)


@dataclass
class Bill:
    surge: D
    quote: D
    actual: D
    charged: D
    night: D
    pickup_wait: D
    mid_wait: D
    toll: D
    gst: D
    rider_total: D
    commission: D
    payout: D
    rule_ids: list


def protect(rules, quote, actual):
    """BR-08 upfront protection: lower actual -> pay actual; up to +20% -> pay the quote;
    beyond +20% -> actual minus 20% of the quote."""
    if actual <= quote:
        return actual
    if actual <= q2(quote * rules.quote_cap_pct / 100):
        return quote
    return actual - q2(quote * rules.protect_excess_pct / 100)


def bill(card, rules, mult, q, arrived, started, ended, actual_km, mid_min, toll):
    """BR-05 order: fare x surge -> cap at quote+20% -> night on the surged fare.
    Waiting and toll are added afterwards, so they are never surged, taxed-as-fare
    or commissioned (BR-07)."""
    ids = ["BR-03", "BR-05"]
    mid_min = D(mid_min)
    ride_min = max(D(0), minutes(ended - started) - mid_min)
    actual = q2(raw_fare(card, actual_km, ride_min) * mult)
    if mult > 1:
        ids.append("BR-02")
    charged = protect(rules, q, actual)
    if charged != actual:
        ids.append("BR-08")
    night = D("0.00")
    if is_night(rules, started):
        night = q2(charged * rules.night_pct / 100)
        ids.append("BR-06")
    wait = minutes(started - arrived)
    billable = max(D(0), wait - rules.free_wait_min).to_integral_value(rounding=ROUND_CEILING)
    pickup = q2(billable * rules.wait_rate)
    mid = q2(max(D(0), mid_min - rules.mid_wait_threshold) * rules.mid_wait_rate)
    if pickup or mid:
        ids.append("BR-07")
    gst = q2((charged + night) * rules.gst_pct / 100)
    total = rupee(charged + night + pickup + mid + toll + gst)
    comm = q2((charged + night) * rules.commission_pct / 100)
    payout = charged + night - comm + pickup + mid + toll
    ids.append("BR-14")
    return Bill(mult, q, actual, charged, night, pickup, mid, q2(toll), gst, total, comm, payout, ids)


def offer_order(rules, nearby, scores):
    """BR-10: drivers inside the radius, nearest first (ties: higher score, then id).
    If the nearest has score < 90 and the second nearest has score >= 90 and is within
    priority_gap_km of the nearest, the second nearest gets the first offer."""
    pool = [(d, km) for d, km in nearby if km <= rules.radius_km]
    pool.sort(key=lambda x: (x[1], -scores[x[0]], x[0]))
    order = [d for d, _ in pool]
    if (len(pool) > 1 and scores[order[0]] < rules.priority_score <= scores[order[1]]
            and pool[1][1] - pool[0][1] <= rules.priority_gap_km):
        order[0], order[1] = order[1], order[0]
    return order


def cancel_fee(rules, cat, accepted_ts, cancel_ts, eta_min):
    """BR-12: free inside the free window or when the driver is far away."""
    elapsed = (cancel_ts - accepted_ts).total_seconds()
    if elapsed <= rules.free_cancel_sec or eta_min > rules.far_eta_min:
        return D("0.00")
    return rules.cancel_fee_sedan if cat == "SEDAN" else rules.cancel_fee


def incentive(rules, weighted, eligible):
    if not eligible:
        return D("0.00")
    for need, amount in rules.incentive_slabs:
        if weighted >= need:
            return q2(amount)
    return D("0.00")
