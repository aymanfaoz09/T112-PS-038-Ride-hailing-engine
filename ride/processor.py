"""Runs the command stream in file order and keeps all state."""
from datetime import timedelta
from decimal import Decimal as D, ROUND_HALF_UP

import inspect

from . import engine as E
from .validation import RideError, dec, whole, stamp, day, need_state, need_order

ZERO = D("0.00")


class Processor:
    def __init__(self, rules, card, drivers, slots, sessions):
        self.r, self.card, self.drv, self.slots, self.sessions = rules, card, drivers, slots, sessions
        self.trips = {}
        self.no_resp = {}          # trip -> set of drivers who time out
        self.offers = {}           # driver -> offers received
        self.accepts = {}          # driver -> offers accepted
        self.penalties = []        # (driver, date, points)
        self.cancel_income = []    # (driver, date, amount)
        self.completed = []        # trip dicts
        self.out_invoices, self.out_daily, self.out_weekly = [], [], []
        self.errors = []           # BR-19: rejected commands

    def run(self, commands):
        for line, name, args in commands:
            fn = getattr(self, "cmd_" + name.lower(), None)
            try:
                if fn is None:
                    raise RideError(f"unknown command {name}")
                need = len(inspect.signature(fn).parameters)
                if len(args) != need:
                    raise RideError(f"{name} needs {need} fields but got {len(args)}")
                fn(*args)
            except RideError as e:
                self.errors.append(dict(line=line, command=name, message=str(e)))

    def _t(self, trip_id):
        if trip_id not in self.trips:
            raise RideError(f"unknown trip {trip_id}")
        return self.trips[trip_id]

    # ---- trip flow (each command validates before it changes anything) ----
    def _driver(self, driver_id):
        if driver_id not in self.drv:
            raise RideError(f"unknown driver {driver_id}")
        return driver_id

    def cmd_request(self, trip_id, when, rider, cat, zone, est_km, est_min, nearby):
        if trip_id in self.trips:
            raise RideError(f"duplicate trip id {trip_id}")
        if cat not in self.card:
            raise RideError(f"unknown category {cat}")
        when = stamp("request time", when)
        km = dec("estimated km", est_km, 0)
        mins = whole("estimated minutes", est_min, 0)
        near = []
        for part in [x for x in nearby.split(",") if x.strip()]:
            if ":" not in part:
                raise RideError(f"nearby driver '{part}' must look like DRV-01:1.25")
            did, dist = part.split(":", 1)
            near.append((self._driver(did.strip()), dec("driver distance", dist, 0)))
        if (zone, E.slot_start(when)) not in self.slots:
            raise RideError(f"no demand/supply data for zone {zone} at {E.slot_start(when)}")
        demand, supply = self.slots[(zone, E.slot_start(when))]
        mult = E.surge_multiplier(self.r, self.card[cat], demand, supply)
        self.trips[trip_id] = dict(id=trip_id, cat=cat, zone=zone, req=when, mult=mult, nearby=near,
                                   quote=E.quote(self.card[cat], self.r, mult, km, mins),
                                   status="REQUESTED", driver=None, accepted=None, arrived=None,
                                   started=None, rating=None, bill=None, fee=ZERO, fee_driver=ZERO)

    def cmd_no_response(self, trip_id, driver):
        t = self._t(trip_id)
        need_state(t, ("REQUESTED",), "record a no-response")
        self.no_resp.setdefault(trip_id, set()).add(self._driver(driver))

    def cmd_accepted(self, trip_id, when):
        t = self._t(trip_id)
        need_state(t, ("REQUESTED",), "accept")
        when = stamp("accept time", when)
        need_order("accept time", when, t["req"], "request time")
        scores = {d: self.score(d, None) for d, _ in t["nearby"]}
        for d in E.offer_order(self.r, t["nearby"], scores):
            self.offers[d] = self.offers.get(d, 0) + 1
            if d in self.no_resp.get(trip_id, ()):
                continue
            self.accepts[d] = self.accepts.get(d, 0) + 1
            t.update(driver=d, accepted=when, status="ACCEPTED")
            return
        t["status"] = "UNMATCHED"

    def cmd_arrived(self, trip_id, when):
        t = self._t(trip_id)
        need_state(t, ("ACCEPTED",), "mark arrived")
        when = stamp("arrival time", when)
        need_order("arrival time", when, t["accepted"], "accept time")
        t.update(arrived=when, status="ARRIVED")

    def cmd_start(self, trip_id, when):
        t = self._t(trip_id)
        need_state(t, ("ARRIVED",), "start")
        when = stamp("start time", when)
        need_order("start time", when, t["arrived"], "arrival time")
        t.update(started=when, status="IN_PROGRESS")

    def cmd_end(self, trip_id, when, km, mid, toll):
        t = self._t(trip_id)
        need_state(t, ("IN_PROGRESS",), "end")
        when = stamp("end time", when)
        need_order("end time", when, t["started"], "start time")
        km, mid, toll = dec("actual km", km, 0), dec("mid-trip wait", mid, 0), dec("toll", toll, 0)
        t["ended"] = when
        t["bill"] = E.bill(self.card[t["cat"]], self.r, t["mult"], t["quote"], t["arrived"],
                           t["started"], when, km, mid, toll)
        t["status"] = "COMPLETED"
        self.completed.append(t)

    def cmd_rate(self, trip_id, stars):
        t = self._t(trip_id)
        need_state(t, ("COMPLETED",), "rate")
        t["rating"] = whole("rating", stars, 1, 5)

    def cmd_cancel_rider(self, trip_id, when, eta):
        t = self._t(trip_id)
        need_state(t, ("REQUESTED", "ACCEPTED", "ARRIVED"), "cancel (rider)")
        when = stamp("cancel time", when)
        eta = whole("driver eta minutes", eta, 0)
        need_order("cancel time", when, t["accepted"] or t["req"], "accept/request time")
        accepted = t["accepted"] is not None
        t["status"] = "CANCELLED_RIDER"
        if not accepted:
            return
        t["fee"] = E.cancel_fee(self.r, t["cat"], t["accepted"], when, eta)
        t["fee_driver"] = E.q2(t["fee"] * self.r.cancel_driver_pct / 100)
        if t["fee"]:
            self.cancel_income.append((t["driver"], when.date(), t["fee_driver"]))

    def cmd_cancel_driver(self, trip_id, when):
        t = self._t(trip_id)
        need_state(t, ("ACCEPTED", "ARRIVED"), "cancel (driver)")
        when = stamp("cancel time", when)
        need_order("cancel time", when, t["accepted"], "accept time")
        t["status"] = "CANCELLED_DRIVER"
        self.penalties.append((t["driver"], when.date(), self.r.cancel_penalty))

    # ---- derived numbers ----
    def score(self, driver, day):
        pts = sum(p for d, dy, p in self.penalties if d == driver and (day is None or dy <= day))
        return self.drv[driver]["score"] - pts

    def _daily(self, driver, day):
        done = [t for t in self.completed if t["driver"] == driver and t["ended"].date() == day]
        weighted = D(0)
        for t in done:
            if t["rating"] is None or t["rating"] < self.r.min_rating:
                continue
            weighted += self.r.peak_weight if E.is_peak(self.r, t["started"]) else D(1)
        score = self.score(driver, day)
        eligible = score >= self.r.incentive_min_score
        earn = sum((t["bill"].payout for t in done), ZERO)
        canc = sum((a for d, dy, a in self.cancel_income if d == driver and dy == day), ZERO)
        inc = E.incentive(self.r, weighted, eligible)
        return dict(done=len(done), weighted=weighted, score=score, eligible=eligible,
                    earn=earn, canc=canc, inc=inc, net=earn + canc + inc)

    # ---- printing ----
    def cmd_print_invoice(self, trip_id):
        t = self._t(trip_id)
        b = t["bill"]
        shown = "UNMATCHED" if t["status"] == "REQUESTED" else t["status"]
        row = dict(trip_id=trip_id, status=shown, driver_id=t["driver"] or "", category=t["cat"],
                   surge_multiplier=f"{t['mult']:.2f}", quote=t["quote"])
        keys = ["actual_fare", "fare_charged", "night_charge", "pickup_wait_charge",
                "mid_trip_wait_charge", "toll", "cancellation_fee", "gst", "rider_total",
                "commission", "driver_payout"]
        row.update({k: ZERO for k in keys})
        row["rule_ids"] = "BR-01"
        if b:
            row.update(actual_fare=b.actual, fare_charged=b.charged, night_charge=b.night,
                       pickup_wait_charge=b.pickup_wait, mid_trip_wait_charge=b.mid_wait, toll=b.toll,
                       gst=b.gst, rider_total=b.rider_total, commission=b.commission,
                       driver_payout=b.payout, rule_ids=";".join(b.rule_ids))
        elif t["status"] == "CANCELLED_RIDER" and t["fee"]:
            comm = t["fee"] - t["fee_driver"]
            row.update(cancellation_fee=t["fee"], rider_total=E.rupee(t["fee"]), commission=comm,
                       driver_payout=t["fee_driver"], rule_ids="BR-12;BR-14")
        elif shown.startswith("CANCELLED"):
            row["rule_ids"] = "BR-12" if t["status"] == "CANCELLED_RIDER" else "BR-13"
        else:
            row["rule_ids"] = "BR-10"
        self.out_invoices.append(row)

    def cmd_print_daily(self, driver, date):
        self._driver(driver)
        dt = day("date", date)
        d = self._daily(driver, dt)
        self.out_daily.append(dict(
            driver_id=driver, date=date, trips_completed=d["done"],
            incentive_trip_count=f"{d['weighted']:.1f}", acceptance_score_eod=d["score"],
            incentive_eligible=str(d["eligible"]).lower(), trip_earnings=d["earn"],
            cancellation_income=d["canc"], incentive=d["inc"], daily_net=d["net"]))

    def cmd_print_weekly(self, driver, week_start):
        self._driver(driver)
        start = stamp("week start", week_start.strip() + " 00:00:00" if len(week_start.strip()) == 10 else week_start)
        end = start + timedelta(days=7)
        mins = sum(int((o - i).total_seconds() // 60) for i, o in self.sessions.get(driver, [])
                   if start <= i < end)
        offers, acc = self.offers.get(driver, 0), self.accepts.get(driver, 0)
        pct = (D(100) * acc / offers) if offers else D(100)
        pct = pct.quantize(D("0.01"), rounding=ROUND_HALF_UP)
        net = sum((self._daily(driver, (start + timedelta(days=i)).date())["net"] for i in range(7)), ZERO)
        ok = mins >= self.r.guarantee_min_online and pct >= self.r.guarantee_min_accept
        top = max(ZERO, self.r.guarantee_amount - net) if ok else ZERO
        self.out_weekly.append(dict(driver_id=driver, week_start=week_start, online_minutes=mins,
                                    acceptance_pct=pct, weekly_net_before_topup=net,
                                    guarantee_topup=top, weekly_net=net + top))
