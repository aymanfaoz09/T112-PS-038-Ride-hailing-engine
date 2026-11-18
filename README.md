# T112 | PS-038 – Ride-Hailing Fare, Surge and Driver Incentive Engine

### A Command-Driven Ride-Hailing Management and Fare Calculation System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Testing](https://img.shields.io/badge/Testing-Pytest-green)
![Interface](https://img.shields.io/badge/Interface-Command--Driven-orange)
![Project](https://img.shields.io/badge/Project-PS--038-purple)

---

## 1. Project Overview

The **Ride-Hailing Fare, Surge and Driver Incentive Engine** is a command-driven software system developed as part of Problem Statement PS-038.

The project focuses on implementing the core backend operations of a ride-hailing platform. It manages the complete lifecycle of a ride, starting from fare estimation and driver allocation to trip completion, final billing, driver earnings, incentives and weekly payment calculations.

In real-world ride-hailing applications, calculating a fare involves more than multiplying distance by a fixed rate. Demand and supply conditions, vehicle categories, peak hours, night charges, waiting time, cancellations, platform commissions and driver incentives all contribute to the final amount.

This project brings these operations together into a structured Python-based engine that processes ride commands, applies predefined business rules, validates events and generates financial reports in CSV format.

The system operates without a graphical user interface. It reads structured input files and processes commands sequentially to simulate the functioning of a ride-hailing platform.

## 2. Problem Statement

**PS-038 – Ride-Hailing Fare, Surge and Driver Incentive Engine**

The objective is to develop a backend engine capable of handling the pricing, matching, billing and incentive mechanisms of a ride-hailing service.

The system must:

- Calculate upfront fare estimates for different vehicle categories.
- Implement dynamic surge pricing based on demand and available supply.
- Match riders with eligible nearby drivers.
- Handle driver acceptance, arrival, trip commencement and completion.
- Calculate actual fares while applying upfront fare protection.
- Account for waiting charges, tolls, night charges and GST.
- Process rider and driver cancellations.
- Calculate driver earnings, platform commission and daily incentives.
- Generate weekly driver statements and apply eligibility-based earnings guarantees.
- Maintain an audit trail of processed commands and rejected operations.

## 3. Project Objectives

The main objectives of this implementation are:

1. **Accurate Fare Calculation:** Implement a structured pricing pipeline that considers distance, duration, vehicle category and applicable charges.

2. **Dynamic Surge Pricing:** Adjust fares according to demand-to-supply ratios within different city zones.

3. **Intelligent Driver Matching:** Select suitable drivers based on proximity, acceptance scores and matching priority rules.

4. **Fare Transparency:** Protect riders from unexpected fare increases through an upfront quote protection mechanism.

5. **Driver Earnings Management:** Calculate trip payouts, cancellation earnings, daily incentives and weekly guarantees.

6. **Business Rule Validation:** Prevent invalid operations and maintain the correct sequence of trip events.

7. **Automated Reporting:** Generate structured CSV reports for trip invoices, daily earnings, weekly statements and processing errors.

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Core application development |
| Decimal | Accurate monetary calculations |
| CSV | Input data processing and report generation |
| Dataclasses | Structured configuration objects |
| Datetime | Trip timestamps, time windows and session calculations |
| Fractions | Accurate demand-to-supply ratio comparisons |
| Pytest | Unit testing and edge-case validation |

The application primarily uses Python's standard library. Pytest is required for executing the automated test suite.

## 5. System Architecture

The project follows a modular architecture in which each component is responsible for a specific operation.

### Architecture Overview

```text
                 INPUT DATA
                      |
          +-----------+-----------+
          |           |           |
       Drivers     Rate Card   Demand & Supply
          |           |           |
          +-----------+-----------+
                      |
                COMMAND FILE
                      |
                      v
                main.py
                      |
                      v
              ride/loaders.py
                      |
              Load and Parse Data
                      |
                      v
              ride/processor.py
                      |
              Command Processing
                      |
          +-----------+-----------+
          |           |           |
       Matching     Pricing    Validation
          |           |           |
          +-----------+-----------+
                      |
                      v
               ride/engine.py
                      |
              Business Rule Engine
                      |
                      v
               OUTPUT REPORTS
                      |
          +-----------+-----------+
          |           |           |
       Invoices     Daily       Weekly
        CSV        Earnings    Statements
```

### Module Description

**1. `main.py` – Application Entry Point**

- Starts the application.
- Loads the required input data.
- Initializes the processing engine.
- Executes the command stream.
- Creates the output directory when necessary.
- Generates the final CSV reports.

**2. `ride/config.py` – Business Rule Configuration**

Contains the configurable business rules and numerical parameters used throughout the application.

These include:

- Surge pricing thresholds.
- Peak-hour time windows.
- Night charge percentages.
- Waiting-time rates.
- Driver matching radius.
- Cancellation penalties and fees.
- Daily incentive slabs.
- Weekly earnings guarantee conditions.

Centralizing these values makes the system easier to maintain and modify.

**3. `ride/loaders.py` – Data Loading and Parsing**

Responsible for reading and loading:

- Vehicle rate cards.
- Driver information.
- Demand and supply records.
- Driver online sessions.
- Ride command files.

It also handles timestamp parsing and supports comma-separated and tab-separated input files.

**4. `ride/engine.py` – Core Business Logic**

Contains the main calculation functions used by the system.

It handles:

- Fare estimation.
- Surge multiplier calculation.
- Actual fare calculation.
- Upfront fare protection.
- Night and waiting charges.
- Driver matching order.
- Cancellation fee calculation.
- Daily incentive calculations.

The pricing and matching functions are kept separate from command processing to make the calculations easier to test.

**5. `ride/processor.py` – Command Processing Engine**

Responsible for maintaining the application state and processing commands in their original file order.

It manages:

- Ride lifecycle and status.
- Driver offers and acceptance.
- Driver arrival and trip commencement.
- Trip completion and billing.
- Rider and driver cancellations.
- Ratings and driver performance.
- Daily and weekly statements.
- Rejected command records.

**6. `ride/validation.py` – Input and Event Validation**

Provides validation functions for numeric values, timestamps, dates and trip states.

It ensures that invalid commands are rejected with meaningful error messages without stopping the processing of subsequent commands.

**7. `tests/` – Automated Testing**

Contains automated test cases covering pricing calculations, matching, cancellations, incentives, weekly guarantees, validations and important boundary conditions.

## 6. Core Functionalities

### 6.1 Multi-Category Fare Calculation

The engine supports four vehicle categories:

| Category | Base Fare (₹) | Base Distance | Per KM (₹) | Per Minute (₹) | Surge Cap |
|---|---:|---:|---:|---:|---:|
| BIKE | 20 | 2 km | 6 | 0 | 1.5x |
| AUTO | 30 | 2 km | 9 | 0 | 1.5x |
| MINI | 50 | 2 km | 12 | 1.5 | 2.0x |
| SEDAN | 80 | 2 km | 15 | 1.5 | 2.0x |

The base fare covers the first 2 kilometres and acts as the minimum fare.

For distances beyond the base distance, additional distance charges are applied. MINI and SEDAN categories also include ride-duration charges.

### 6.2 Dynamic Surge Pricing

Surge pricing is calculated using the demand-to-supply ratio of a particular zone and 15-minute time slot.

The system uses the following thresholds:

| Demand/Supply Ratio | Surge Multiplier |
|---|---:|
| Below 1.2 | 1.0x |
| 1.2 to below 1.6 | 1.3x |
| 1.6 to below 2.0 | 1.6x |
| 2.0 and above | 2.0x |

The calculated multiplier is restricted by the maximum surge cap of the selected vehicle category.

If the available supply is zero, the highest surge band is selected before applying the category cap.

### 6.3 Upfront Fare Estimation and Protection

Before a trip begins, the system calculates an estimated fare using the estimated distance, duration, vehicle category and applicable surge multiplier.

The estimated fare is stored as the trip quote.

When the trip is completed, the engine calculates the actual fare using the recorded trip details.

The upfront protection mechanism follows three conditions:

- If the actual fare is lower than the quoted fare, the rider pays the actual fare.
- If the actual fare is higher than the quote but within 20% of it, the rider pays the original quoted fare.
- If the actual fare exceeds the quote by more than 20%, the rider pays the actual fare minus 20% of the original quote.

This mechanism helps maintain fare transparency and prevents unexpected increases beyond the defined protection limit.

### 6.4 Driver Matching and Allocation

The matching engine selects drivers based on their distance from the pickup location and acceptance score.

The implemented matching rules include:

- Only drivers within a 3 km radius are considered.
- Drivers are normally arranged in increasing order of distance.
- When the nearest driver has an acceptance score below 90 and the second-nearest driver has a score of at least 90, the second driver may receive priority if they are within 0.5 km of the nearest driver.
- Ties in distance are resolved using higher acceptance scores and then driver IDs.
- Drivers who do not respond to an offer are skipped so the next eligible driver can be considered.

If no eligible driver is available, the request is marked as unmatched.

### 6.5 Trip Lifecycle Management

The application maintains the status of each ride throughout its lifecycle.

The supported flow is:

```text
REQUESTED
    |
    v
ACCEPTED
    |
    v
ARRIVED
    |
    v
IN_PROGRESS
    |
    v
COMPLETED
```

The system also supports cancellation and unmatched outcomes.

Each event is validated against the current trip status. For example, a trip cannot be completed before it has started, and a driver cannot mark arrival before accepting the ride.

### 6.6 Night Charges and Waiting Charges

**Night Charges**

A 25% night charge is applied to the protected fare when the pickup time falls within the defined night window of 23:00 to 05:00.

**Pickup Waiting Charges**

- First 3 minutes are free.
- Additional waiting time is charged at ₹1 per minute.
- Partial additional minutes are rounded up.

**Mid-Trip Waiting Charges**

- First 5 minutes are free.
- Additional waiting time is charged at ₹2 per minute.

Waiting charges and tolls are added separately after the fare calculation. They are not subjected to surge pricing or platform commission.

### 6.7 Cancellation Management

The engine supports both rider-initiated and driver-initiated cancellations.

**Rider Cancellation**

Cancellation fees depend on the elapsed time after driver acceptance and the driver's estimated distance from the pickup location.

- Cancellation within 2 minutes of acceptance is free.
- Cancellation when the driver is more than 10 minutes away is free.
- Otherwise, the standard cancellation fee is ₹30.
- For SEDAN rides, the cancellation fee is ₹50.

The driver receives 80% of an applicable rider cancellation fee.

**Driver Cancellation**

When a driver cancels an accepted ride:

- The driver's acceptance score is reduced by 5 points.
- The cancellation is recorded against the date.
- Drivers with a score below 70 become ineligible for that day's incentive.

A score of exactly 70 remains eligible.

### 6.8 GST and Platform Commission

The system calculates GST and platform commission separately.

- GST is calculated at 5% on the fare charged after protection and applicable night charges.
- Platform commission is 20% of the fare charged after protection and applicable night charges.
- Waiting charges and tolls are excluded from the commission calculation.

The remaining amount, along with applicable waiting charges and tolls, contributes to the driver's trip payout.

### 6.9 Daily Driver Incentives

The engine calculates driver incentives based on completed and qualifying trips.

Only trips with a rider rating of 4 or above are counted.

Trips beginning during the defined peak-hour windows receive a weighted value of 1.5 instead of 1.

The incentive slabs are:

| Qualifying Weighted Trips | Daily Incentive |
|---|---:|
| 12 or more | ₹300 |
| 20 or more | ₹700 |
| Below 12 | ₹0 |

The incentive slabs are non-cumulative. The highest eligible slab is awarded.

Drivers must also maintain an acceptance score of at least 70 to qualify.

### 6.10 Weekly Driver Earnings Guarantee

The weekly statement includes an earnings guarantee for eligible drivers.

A driver qualifies when both conditions are satisfied:

- At least 60 hours of online time during the week.
- An acceptance percentage of at least 85%.

Eligible drivers are guaranteed a weekly net earning of ₹9,000.

If their calculated weekly earnings are below ₹9,000, the system calculates a top-up amount to meet the guarantee.

The weekly report includes the online minutes, acceptance percentage, earnings before top-up, guarantee top-up and final weekly net earnings.

## 7. Input Data Structure

The project uses structured input files stored inside the `data/` directory.

| File | Description |
|---|---|
| `zones.csv` | Contains the five city zones used in the simulation. |
| `rate_card.csv` | Stores fare information for all four vehicle categories. |
| `drivers.csv` | Contains driver IDs, categories, vehicle numbers, starting acceptance scores and home zones. |
| `demand_supply.csv` | Contains demand and supply information for each zone in 15-minute intervals. |
| `driver_sessions.csv` | Records driver login and logout sessions for weekly online-hour calculations. |
| `commands.txt` | Contains the chronological stream of ride requests, events, cancellations, ratings and report-generation commands. |

The supplied sample data covers seven days, from 12 October 2026 to 18 October 2026.

It contains 150 trip requests, 20 cancellations and 3,360 demand/supply records.

### Command File Format

The system reads one command per line using the following structure:

`COMMAND_NAME|argument1|argument2|...`

The supported commands are:

| Command | Purpose |
|---|---|
| `REQUEST` | Creates a ride request and calculates its upfront quote. |
| `NO_RESPONSE` | Records a driver who does not respond to an offer. |
| `ACCEPTED` | Records driver acceptance. |
| `ARRIVED` | Records driver arrival at pickup. |
| `START` | Marks the beginning of the ride. |
| `END` | Completes the ride and calculates the final bill. |
| `RATE` | Records the rider's rating. |
| `CANCEL_RIDER` | Processes rider-initiated cancellation. |
| `CANCEL_DRIVER` | Processes driver-initiated cancellation. |
| `PRINT_INVOICE` | Generates a trip invoice record. |
| `PRINT_DAILY` | Generates a driver's daily earnings statement. |
| `PRINT_WEEKLY` | Generates a driver's weekly earnings statement. |

Commands are processed sequentially. Blank lines and lines beginning with `#` are ignored.

## 8. Output Reports

After processing the command stream, the application generates four CSV files inside the `out/` directory.

### 1. `trip_invoices.csv`

Contains trip-level billing information, including:

- Trip ID and status.
- Assigned driver and vehicle category.
- Surge multiplier.
- Estimated and actual fares.
- Protected fare charged.
- Night and waiting charges.
- Tolls and cancellation fees.
- GST and rider's final payable amount.
- Platform commission.
- Driver payout.
- Applied business-rule IDs.

### 2. `driver_daily.csv`

Contains daily driver performance and earnings information, including:

- Completed trips.
- Qualifying weighted incentive trips.
- End-of-day acceptance score.
- Incentive eligibility.
- Trip earnings.
- Cancellation income.
- Daily incentive.
- Final daily net earnings.

### 3. `driver_weekly.csv`

Contains weekly driver statements, including:

- Total online minutes.
- Acceptance percentage.
- Weekly earnings before top-up.
- Weekly guarantee top-up.
- Final weekly net earnings.

### 4. `errors.csv`

Maintains an audit record of rejected commands.

Each error record contains:

- Original command line number.
- Command name.
- Description of the validation or processing error.

Invalid commands are logged without stopping the remaining command stream.

## 9. Project Directory Structure

```text
PS-038-Ride-Hailing-Fare-Engine/
│
├── data/
│   ├── commands.txt
│   ├── demand_supply.csv
│   ├── drivers.csv
│   ├── driver_sessions.csv
│   ├── rate_card.csv
│   ├── zones.csv
│   └── README.md
│
├── ride/
│   ├── __init__.py
│   ├── config.py
│   ├── engine.py
│   ├── loaders.py
│   ├── processor.py
│   └── validation.py
│
├── tests/
│   ├── test_rules.py
│   ├── test_rule_coverage.py
│   └── test_week3.py
│
├── out/
│   ├── driver_daily.csv
│   ├── driver_weekly.csv
│   ├── errors.csv
│   └── trip_invoices.csv
│
├── main.py
├── pytest.ini
└── README.md
```

## 10. Installation and Setup

### Prerequisites

Before running the project, ensure that the following are installed:

- Python 3.10 or above.
- pip (Python package installer).
- A code editor such as Visual Studio Code.
- Git (optional, for version control).

### Step 1: Clone the Repository

```bash
git clone <repository-url>
```

### Step 2: Navigate to the Project Directory

```bash
cd PS-038-Ride-Hailing-Fare-Surge-and-Driver-Incentive-Engine
```

### Step 3: Install Testing Dependency

```bash
pip install pytest
```

The application itself uses Python standard-library modules and does not require additional runtime packages.

### Step 4: Run the Application

```bash
python main.py
```

The application reads input files from the `data/` directory and generates reports in the `out/` directory.

Optional custom input and output directories can also be supplied:

```bash
python main.py data out
```

### Step 5: Run Automated Tests

```bash
pytest
```

This executes the unit tests and the additional edge-case coverage tests.

## 11. Testing and Edge-Case Coverage

Testing is an important part of the project because fare calculations and driver earnings depend on precise business-rule conditions.

The project includes test cases for the following scenarios:

| Test Area | Scenarios Covered |
|---|---|
| Surge Pricing | Surge thresholds, boundary conditions and category caps. |
| Fare Calculation | Base fare, distance, duration and minimum fare. |
| Upfront Protection | Actual fare below, within and above the 20% protection limit. |
| Night Pricing | Night window boundaries and night charges. |
| Driver Matching | Radius restrictions, priority scores and no-response scenarios. |
| Cancellations | Rider cancellation fees, driver penalties and fee distribution. |
| Driver Incentives | Qualifying ratings, peak-hour weighting and incentive slabs. |
| Weekly Guarantee | Minimum online hours and acceptance percentage. |
| Input Validation | Invalid numbers, negative values, timestamps and unknown IDs. |
| Trip Lifecycle | Invalid event sequences and duplicate trip IDs. |
| Financial Accuracy | Decimal calculations and half-up rounding. |

### Important Edge Cases

The implementation also tests several carefully selected boundary scenarios:

- A trip with an actual distance of exactly 2.0 km.
- Demand-to-supply ratio exactly equal to 1.2.
- A pickup occurring exactly at 23:00.
- An actual fare exactly 20% above the quoted fare.
- Rider cancellation exactly 2 minutes after acceptance.
- A driver acceptance score exactly equal to 70.
- A trip ending exactly at 10:00 after starting at 09:50.
- A driver with 59 hours and 59 minutes of weekly online time.

These scenarios help verify that the engine handles boundary conditions consistently instead of relying only on ordinary input values.

## 12. Business Rule Decisions and Assumptions

Some business-rule details require explicit interpretation when translating the problem statement into executable logic.

The implementation centralizes these decisions in `ride/config.py` and documents the relevant choices in the code.

Important implementation decisions include:

1. **Surge Boundaries:** Surge thresholds are inclusive, meaning a ratio exactly equal to a threshold enters that higher surge band.

2. **Fare Protection:** The 20% protection comparison is performed using amounts rounded to two decimal places.

3. **Night Charges:** The night charge is applied to the protected fare after surge pricing.

4. **Commission and GST:** Both are calculated using the protected fare and applicable night charge, excluding waiting charges and tolls.

5. **Driver Matching Priority:** A high-acceptance-score second-nearest driver may receive priority when within 0.5 km of the nearest driver.

6. **Cancellation Conditions:** The 2-minute free cancellation window is inclusive, while the free-distance condition applies when the driver is more than 10 minutes away.

7. **Peak-Hour Classification:** Peak-hour eligibility is determined using the trip's start time.

These decisions are configurable and should be reviewed against the final problem-statement interpretation if business rules are revised.

## 13. Key Features and Implementation Highlights

The major technical highlights of this project include:

- Modular Python architecture separating configuration, business logic, validation and command processing.
- Centralized business-rule configuration for easier maintenance.
- Use of `Decimal` for accurate financial calculations.
- Use of `Fraction` for precise demand-to-supply threshold comparisons.
- Sequential event processing with trip-state validation.
- Separate calculations for rider payments, driver earnings and platform commission.
- Structured CSV-based input and output handling.
- Automated unit testing and boundary-condition coverage.
- Error logging that allows processing to continue after invalid commands.

## 14. Future Enhancements

The current implementation focuses on the backend fare, matching and incentive engine. The following improvements could extend the system further:

- Develop a web-based dashboard for riders, drivers and administrators.
- Integrate a real-time GPS and location-tracking service.
- Implement live driver availability and automated dispatch.
- Connect a database for persistent trip and driver records.
- Introduce APIs for integration with mobile applications.
- Add real-time demand forecasting for improved surge pricing.
- Develop analytics dashboards for driver performance and business revenue.
- Implement authentication and role-based access control.

## 15. Conclusion

The Ride-Hailing Fare, Surge and Driver Incentive Engine demonstrates how the essential backend operations of a ride-hailing platform can be implemented through a structured, rule-based software system.

By combining dynamic pricing, driver allocation, trip lifecycle management, cancellation handling, fare protection and driver incentive calculations, the project addresses multiple interconnected requirements of a simulated ride-hailing environment.

The modular architecture, structured data processing, validation mechanisms and automated test cases provide a foundation for maintaining correctness and extending the system with additional features.

The project also demonstrates the practical application of Python programming, financial calculations, data handling, algorithmic decision-making and software testing in solving a real-world mobility problem.

---

**Project:** PS-038 – Ride-Hailing Fare, Surge and Driver Incentive Engine  
**Team:** T112  
**Department:** Information Science and Engineering  
**Project Type:** Backend Software Engineering  
**Primary Language:** Python