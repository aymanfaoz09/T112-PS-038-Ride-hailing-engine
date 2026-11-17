"""BR-19: every bad input becomes a RideError with a clear message. The processor
catches it, logs it to errors.csv and carries on with the next command."""
from decimal import Decimal as D, InvalidOperation

from .loaders import ts


class RideError(Exception):
    pass


def dec(field, text, minimum=None):
    try:
        v = D(str(text).strip())
    except InvalidOperation:
        raise RideError(f"{field} '{text}' is not a number")
    if not v.is_finite():
        raise RideError(f"{field} '{text}' is not a finite number")
    if minimum is not None and v < minimum:
        raise RideError(f"{field} {v} must be at least {minimum}")
    return v


def whole(field, text, minimum=None, maximum=None):
    try:
        v = int(str(text).strip())
    except ValueError:
        raise RideError(f"{field} '{text}' is not a whole number")
    if minimum is not None and v < minimum:
        raise RideError(f"{field} {v} must be at least {minimum}")
    if maximum is not None and v > maximum:
        raise RideError(f"{field} {v} must be at most {maximum}")
    return v


def stamp(field, text):
    try:
        return ts(text)
    except ValueError:
        raise RideError(f"{field} '{text}' is not a valid timestamp")


def day(field, text):
    return stamp(field, text.strip() + " 00:00:00").date() if len(text.strip()) == 10 else stamp(field, text).date()


def need_state(trip, allowed, action):
    if trip["status"] not in allowed:
        raise RideError(f"{trip['id']}: cannot {action} while trip is {trip['status']}")


def need_order(field, later, earlier, earlier_name):
    if earlier is not None and later < earlier:
        raise RideError(f"{field} {later} is before {earlier_name} {earlier}")
