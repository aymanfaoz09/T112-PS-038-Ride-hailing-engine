# T112-PS-038 Ride-Hailing Fare, Surge and Driver Incentive Engine

    python main.py     # reads data/, writes out/trip_invoices.csv, driver_daily.csv, driver_weekly.csv
    pytest             # unit tests plus the planted edge cases EC-01..EC-08

Layout: ride/config.py (all rule numbers), ride/loaders.py (CSV and command parsing),
ride/engine.py (pure pricing, surge, matching, cancellation, incentive),
ride/processor.py (command stream and statements), main.py (CSV output).

Fare pipeline: fare x surge -> cap at quote + 20% -> night charge on that surged fare;
pickup wait, mid-trip wait and toll are added afterwards, so they are never surged or commissioned.
Money is Decimal, rounded half-up to the paisa; rider_total to the rupee.

Rules marked ASSUMED in ride/config.py are guesses until checked against the brief.