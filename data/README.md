# PS-038 – Ride-Hailing Fare, Surge and Driver Incentive Engine — Sample Data Pack

Prepared by 10 SECONDS for Team T112.

## Files

| File | What it holds | Row count |
|---|---|---|
| `zones.csv` | 5 city zones | 5 data rows |
| `rate_card.csv` | Base fare, per-km and per-minute rates and surge cap per category | 4 data rows |
| `drivers.csv` | 20 drivers with category and acceptance score at the start of the week | 20 data rows |
| `demand_supply.csv` | Demand and supply counters per zone per 15-minute slot (96 a day for 7 days) | 3360 data rows |
| `driver_sessions.csv` | Online sessions per driver (weekly online hours) | 250 data rows |
| `commands.txt` | 150 trip requests over 7 days (20 cancellations) with offer responses, arrival, start, end, ratings and print requests | 1146 command lines (excluding comments) |

Row numbers quoted below are 1-based data-row numbers (the header is row 0). Line numbers for `commands.txt` are physical line numbers including comment lines.

## Column reference

Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals with 2 places (no commas, no symbol); percentages as plain numbers (12.5 means 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix. An empty cell means "not applicable" and only appears in columns whose notes say so.

### `zones.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| zone_id | string | ZN-n | — | primary key |
| zone_name | string | — | — | — |

### `rate_card.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| category | enum | — | BIKE, AUTO, MINI, SEDAN | primary key |
| base_fare | decimal | Rs | — | covers the first base_km; also the minimum fare |
| base_km | decimal | km | — | — |
| per_km | decimal | Rs | — | beyond base_km |
| per_min | decimal | Rs | — | ride time, MINI/SEDAN only |
| surge_cap | decimal | — | — | maximum multiplier for the category |

### `drivers.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| driver_id | string | DRV-nn | — | primary key |
| driver_name | string | — | — | — |
| category | string | — | rate_card.csv | — |
| vehicle_no | string | — | — | — |
| acceptance_score_start | int | points | 0-100 | score at 2026-10-12 00:00 |
| home_zone | string | — | zones.csv | informational |

### `demand_supply.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| zone_id | string | — | zones.csv | — |
| slot_start | timestamp | — | every 15 min | slot covers [slot_start, slot_start + 15 min) |
| demand | int | requests | — | — |
| supply | int | drivers | — | ratio = demand / supply |

### `driver_sessions.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| session_id | string | SES-nnnn | — | — |
| driver_id | string | — | drivers.csv | — |
| login_ts | timestamp | — | — | — |
| logout_ts | timestamp | — | — | online time = logout - login |

## Command file format

`commands.txt` holds one command per line in the form `COMMAND_NAME|arg1|arg2|...`. Commands must be processed strictly in file order. Lines starting with `#` are comments and blank lines are ignored. An empty argument (two adjacent `|`) means "not supplied". Every command used in this pack:

| Command | Arguments (in order) | Meaning |
|---|---|---|
| `REQUEST` | `trip_id|ts|rider_id|category|pickup_zone|est_km|est_min|nearby_drivers` | Quote (locked 2 min) and start matching; nearby_drivers = `DRIVER:km` joined by `,` |
| `NO_RESPONSE` | `trip_id|driver_id` | This driver lets any offer for the trip time out after 15 s |
| `ACCEPTED` | `trip_id|ts` | The driver currently holding the offer accepts |
| `ARRIVED` | `trip_id|ts` | Driver at pickup (pickup waiting starts) |
| `START` | `trip_id|ts` | Rider picked up (pickup time for the night rule) |
| `END` | `trip_id|ts|actual_km|mid_trip_wait_min|toll` | Trip completed; bill it |
| `RATE` | `trip_id|stars` | Rider's rating of the driver for the trip (1-5) |
| `CANCEL_RIDER` | `trip_id|ts|driver_eta_min` | Rider cancels; driver_eta_min = driver's distance from pickup in minutes at that moment |
| `CANCEL_DRIVER` | `trip_id|ts` | Driver cancels after accepting |
| `PRINT_INVOICE` | `trip_id` | Print the trip invoice |
| `PRINT_DAILY` | `driver_id|date` | Print the driver's daily earnings |
| `PRINT_WEEKLY` | `driver_id|week_start` | Print the driver's weekly statement |

## Planted scenarios

Every edge case in the brief, mapped to the exact record where it occurs, followed by extra traps.

- **EC-01 Trip of exactly 2.0 km**
  - MINI trip with actual distance exactly 2.0 km -> distance part is the base fare only; 11 ride minutes still billed at Rs 1.5/min — commands.txt line 204 (`REQUEST|TRP-0034|2026-10-13 14:07:20|RDR-2337|MINI|ZN-1|2.0|9|DRV-15:0.49,DRV-12:1.45,DRV-16:3.53`); commands.txt line 210 (`END|TRP-0034|2026-10-13 14:28:51|2.00|0|0.00`)
- **EC-02 Demand/supply ratio exactly 1.2 for a BIKE in a 2.0 surge zone**
  - ZN-4 on 2026-10-14: slot 18:30 has demand 60 / supply 50 = exactly 1.2 (-> 1.3) while the surrounding slots are 110/50 = 2.2 (-> 2.0, BIKE capped at 1.5); one BIKE request in each — demand_supply.csv row 2283 (2026-10-14 18:30:00); commands.txt line 422 (`REQUEST|TRP-0068|2026-10-14 18:33:40|RDR-2445|BIKE|ZN-4|4.6|16|DRV-04:0.60,DRV-01:1.64,DRV-02:2.92`); commands.txt line 434 (`END|TRP-0068|2026-10-14 18:52:55|4.30|0|0.00`); commands.txt line 432 (`REQUEST|TRP-0070|2026-10-14 18:49:05|RDR-8449|BIKE|ZN-4|3.9|14|DRV-03:0.90,DRV-02:1.33,DRV-04:3.02`); commands.txt line 440 (`END|TRP-0070|2026-10-14 19:11:21|4.60|0|0.00`)
- **EC-03 Pickup at exactly 23:00**
  - SEDAN pickup (START) at exactly 23:00:00 -> night charge applies; control: AUTO pickup at 05:00:00 -> outside 23:00–05:00 — commands.txt line 599 (`REQUEST|TRP-0095|2026-10-15 22:51:10|RDR-3208|SEDAN|ZN-5|18.5|38|DRV-18:0.62,DRV-17:2.48,DRV-19:3.13`); commands.txt line 603 (`END|TRP-0095|2026-10-15 23:55:00|17.50|0|70.00`); commands.txt line 632 (`REQUEST|TRP-0097|2026-10-16 04:48:00|RDR-4809|AUTO|ZN-1|5.2|17|DRV-09:0.56,DRV-10:1.61,DRV-06:1.86`); commands.txt line 636 (`END|TRP-0097|2026-10-16 05:17:00|4.90|4|0.00`)
- **EC-04 Actual fare exactly 20% above quote**
  - AUTO, no surge (ZN-2 ratio 0.77): estimated 12.0 km -> quote Rs 120.00; actual 14.67 km -> Rs 144.03 (Rs 144 after rounding = exactly 1.2 x quote) and twin at 14.66 km -> Rs 143.94 — decide at which precision the +20% test runs — commands.txt line 164 (`REQUEST|TRP-0027|2026-10-13 11:04:00|RDR-3090|AUTO|ZN-2|12.0|30|DRV-07:0.57,DRV-09:2.32,DRV-08:2.92`); commands.txt line 179 (`END|TRP-0027|2026-10-13 11:57:00|14.67|6|0.00`); commands.txt line 166 (`REQUEST|TRP-0028|2026-10-13 11:09:30|RDR-6291|AUTO|ZN-2|12.0|30|DRV-08:0.73,DRV-06:1.38,DRV-10:3.11`); commands.txt line 178 (`END|TRP-0028|2026-10-13 11:53:46|14.66|0|0.00`)
- **EC-05 Rider cancels at exactly 2 minutes after acceptance with driver 10 minutes away**
  - Rider cancels at acceptance + 120 s with driver_eta_min 10 -> neither 'within 2 minutes' nor 'more than 10 minutes away' is clearly met — commands.txt line 52 (`REQUEST|TRP-0010|2026-10-12 19:12:00|RDR-4421|MINI|ZN-1|6.0|22|DRV-14:0.34,DRV-11:1.50,DRV-16:1.84`); commands.txt line 54 (`CANCEL_RIDER|TRP-0010|2026-10-12 19:14:07|10`)
- **EC-06 Driver score exactly 70 after a cancellation**
  - DRV-06 starts the week with acceptance score 75; driver-cancels on 2026-10-15 -> 70 (not below 70) -> still eligible for the day's incentive — drivers.csv row 6 (DRV-06); commands.txt line 503 (`REQUEST|TRP-0078|2026-10-15 09:05:00|RDR-2485|AUTO|ZN-3|7.5|25|DRV-06:0.79,DRV-09:1.99,DRV-08:3.19`); commands.txt line 505 (`CANCEL_DRIVER|TRP-0078|2026-10-15 09:06:41`)
- **EC-07 Peak-hour trip ending at 10:00 (started 09:50)**
  - DRV-11: trip START 09:50:00, END 10:00:00 — does it count as a peak trip (1.5)? On 2026-10-14 this driver has many other trips; whether the 12-trip slab is reached depends on it — commands.txt line 334 (`REQUEST|TRP-0052|2026-10-14 09:46:30|RDR-8353|MINI|ZN-4|3.4|10|DRV-11:0.33,DRV-13:1.95,DRV-12:2.17`); commands.txt line 339 (`END|TRP-0052|2026-10-14 10:00:00|3.20|0|0.00`)
- **EC-08 Driver with 59 h 59 min online for the weekly guarantee**
  - DRV-16 is online 59 h 59 min in the week (sum of driver_sessions.csv) -> no weekly guarantee; DRV-19 is online exactly 60 h 00 min with acceptance >= 85 -> eligible — driver_sessions.csv: 14 rows for DRV-16 (SES-0010 … SES-0246); driver_sessions.csv: 14 rows for DRV-19 (SES-0007 … SES-0241)
- **Extra traps (not in the brief, but realistic):**
  - SEDAN rider cancellation 5 min after acceptance with driver 4 min away -> Rs 50, of which 80% to the driver — commands.txt line 824 (`REQUEST|TRP-0127|2026-10-17 13:20:00|RDR-9612|SEDAN|ZN-5|32.0|50|DRV-17:0.39,DRV-18:1.39,DRV-20:1.91`); commands.txt line 826 (`CANCEL_RIDER|TRP-0127|2026-10-17 13:25:09|4`)
  - Pickup wait 7 min (first 3 free -> 4 x Rs 1) and 8 min of mid-trip stops (> 5 -> charged), plus a Rs 35 toll — none of these is surged or commissioned — commands.txt line 687 (`REQUEST|TRP-0108|2026-10-16 15:40:00|RDR-1350|MINI|ZN-3|9.0|28|DRV-15:0.67,DRV-14:1.52,DRV-16:2.44`); commands.txt line 695 (`END|TRP-0108|2026-10-16 16:17:29|10.10|8|35.00`)
  - No driver within 3 km (nearest 3.40 km) -> request cannot be matched — commands.txt line 925 (`REQUEST|TRP-0143|2026-10-18 11:00:00|RDR-7194|BIKE|ZN-2|5.0|15|DRV-04:3.40,DRV-03:4.47`)
  - Nearest MINI driver is 0.60 km away but the second-nearest (0.95 km) has acceptance >= 90 -> the second-nearest gets the first offer; he times out after 15 s and the offer moves on — commands.txt line 232 (`REQUEST|TRP-0038|2026-10-13 17:22:00|RDR-8835|MINI|ZN-4|7.2|26|DRV-13:0.60,DRV-12:0.95,DRV-15:2.22`); commands.txt line 237 (`END|TRP-0038|2026-10-13 17:51:32|7.00|4|0.00`)
  - ZN-1 slot 2026-10-15 08:00:00: demand 80 / supply 50 = exactly 1.6 (band boundary 1.3 vs 1.6) with a SEDAN request in it — demand_supply.csv row 321 (2026-10-15 08:00:00); commands.txt line 496 (`REQUEST|TRP-0077|2026-10-15 08:06:00|RDR-4530|SEDAN|ZN-1|8.4|27|DRV-18:0.84,DRV-17:2.42,DRV-20:3.20`); commands.txt line 501 (`END|TRP-0077|2026-10-15 08:41:22|8.90|4|0.00`)
  - DRV-11's trip TRP-0054 on 2026-10-14 is rated 3 by the rider -> does not count toward the daily incentive — commands.txt line 350 (`RATE|TRP-0054|3`)

## What is NOT in this pack

Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-nn). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation

Produce these CSV files (header row, same conventions as above, rows sorted as stated). Where the brief is silent on a format detail the choice below is binding for evaluation.

### `trip_invoices.csv`

One row per PRINT_INVOICE.

Columns, in order: `trip_id`, `status`, `driver_id`, `category`, `surge_multiplier`, `quote`, `actual_fare`, `fare_charged`, `night_charge`, `pickup_wait_charge`, `mid_trip_wait_charge`, `toll`, `cancellation_fee`, `gst`, `rider_total`, `commission`, `driver_payout`, `rule_ids`

### `driver_daily.csv`

One row per PRINT_DAILY.

Columns, in order: `driver_id`, `date`, `trips_completed`, `incentive_trip_count`, `acceptance_score_eod`, `incentive_eligible`, `trip_earnings`, `cancellation_income`, `incentive`, `daily_net`

### `driver_weekly.csv`

One row per PRINT_WEEKLY.

Columns, in order: `driver_id`, `week_start`, `online_minutes`, `acceptance_pct`, `weekly_net_before_topup`, `guarantee_topup`, `weekly_net`

Binding choices: `status` is COMPLETED, CANCELLED_RIDER, CANCELLED_DRIVER or UNMATCHED; `incentive_trip_count` may be fractional (1 dp); online_minutes is an integer; acceptance_pct = accepted offers / offers received in the week (2 dp); rider_total is rounded to the rupee, everything else to the paisa.

