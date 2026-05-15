# Supplier Master Table

Table: `supplier_master`

| Column                        | Type    | Purpose                     |
|------------------------------|---------|-----------------------------|
| `supplier_id`                | string  | unique supplier             |
| `supplier_name`              | string  | supplier                    |
| `supplier_category`          | string  | electronics, metal etc      |
| `country`                    | string  | region risk                 |
| `city`                       | string  | logistics mapping           |
| `criticality_level`          | int     | business importance         |
| `alternate_supplier_available` | boolean | dependency risk             |
| `onboarding_time_days`       | int     | replacement time            |
| `contract_value`             | float   | financial exposure          |
| `payment_terms_days`         | int     | financial relationship      |



## Example correlations

- High `criticality_level`
  - usually higher `contract_value`
  - often fewer alternates available
- `supplier_category` = electronics
  - longer `onboarding_time_days`
  - more Asian supplier concentration
- `payment_terms_days`
  - often 30 / 45 / 60 / 90
  - larger suppliers may negotiate longer terms
- `alternate_supplier_available` = false
  - usually higher business risk
  - maybe higher onboarding time





## Supplier category distribution

Weighted distribution:

| Category    | Weight |
|-------------|--------|
| electronics | 30%    |
| metals      | 20%    |
| packaging   | 15%    |
| chemicals   | 10%    |
| plastics    | 10%    |
| logistics   | 10%    |
| textiles    | 5%     |

## Onboarding time ranges

Suggested typical ranges for `onboarding_time_days`, with randomness generated via normal distribution around the category mean:

| Category    | Typical Range (days) |
|-------------|----------------------|
| electronics | 60–180               |
| chemicals   | 45–120               |
| packaging   | 15–45                |
| logistics   | 7–30                 |

Use a normal distribution centered on the category mean and clipped to the category range to add realistic variation.

## Criticality level distribution

Weighted distribution:

| Criticality level | Weight |
|-------------------|--------|
| 1                 | 10%    |
| 2                 | 20%    |
| 3                 | 35%    |
| 4                 | 25%    |
| 5                 | 10%    |

## Contract value distribution

Weighted distribution:

| Contract value category | Weight |
|-------------------------|--------|
| small                   | 80%    |
| medium                  | 15%    |
| very large              | 5%     |

## Payment terms distribution

Use realistic discrete values: 15, 30, 45, 60, 90

Weighted distribution:

| Days | Weight |
|------|--------|
| 30   | 40%    |
| 45   | 25%    |
| 60   | 25%    |
| 90   | 10%    |


# Purchase Order Table

Table: `purchase_orders`

| Column                        | Type    |
|------------------------------|---------|
| `po_id`                      | string  |
| `supplier_id`                | string  |
| `order_date`                 | date    |
| `expected_delivery_date`     | date    |
| `actual_delivery_date`       | date    |
| `order_quantity`             | float   |
| `received_quantity`          | float   |
| `order_value`                | float   |
| `component_id`               | string  |



## Key principle

If Supplier A is:

- high `criticality_level`
- overseas
- long `onboarding_time_days`
- electronics-focused

…their POs should naturally show:

- longer lead times
- larger order values
- higher delay volatility
- fewer suppliers for the same component


## Core Relationships

supplier_master
    ↓
purchase_orders
supplier_id

Foreign key from supplier_master.

supplier_category ↔ component_id

- `component_id` should align with `supplier_category` so electronics suppliers generate electronic component POs, packaging suppliers generate packaging component POs, etc.
- This correlation keeps purchase orders consistent with the supplier catalog and avoids mismatched parts.

## Realistic Business Rules

### A. Order Frequency by Supplier

- Not all suppliers receive equal orders.
- Typical enterprise pattern:
  - top 10% suppliers → 50% of PO value
  - long-tail suppliers → infrequent small orders
- Use weighted sampling.

### B. Lead Time Logic

`expected_delivery_date = order_date + supplier/category lead time`

Example baseline:

| Category     | Typical Lead Time |
|--------------|-------------------|
| electronics  | 30–90 days        |
| metals       | 15–45 days        |
| packaging    | 7–20 days         |
| logistics    | 1–7 days          |

- International suppliers increase lead time.

### C. Actual Delivery Variance

Real suppliers are late. Constantly. Civilization runs on “slightly delayed.”

Typical:

- 65% on time
- 25% late
- 10% early

Late delivery severity influenced by:

- country risk
- criticality
- category

Example:

- China electronics supplier:
  - expected = 45 days
  - actual = expected + random(-2 to +20)

### D. Received Quantity Logic

Partial receipts are VERY common.

Rules:

- 85% fully received
- 10% partial
- 5% over/under adjustments

Example:

- `received_quantity <= order_quantity`
- unless:
  - tolerances
  - packaging variance
  - overdelivery allowed

### E. Order Value Correlation

- `order_value = order_quantity × component unit price`
- Do NOT randomize independently.
- That instantly exposes fake data.

### Add seasonality.

- Q4 spikes
- month-end spikes
- fiscal year purchasing surges

| Column                  | Logic                          |
|-------------------------|--------------------------------|
| po_id                   | unique sequential             |
| supplier_id             | weighted FK                   |
| order_date              | random with seasonality       |
| expected_delivery_date  | based on category + geography |
| actual_delivery_date    | expected ± delay variance     |
| order_quantity          | category dependent            |
| received_quantity       | tied to delivery quality      |
| order_value             | qty × unit price              |
| component_id            | constrained by supplier category |

| Scenario                  | Probability |
|---------------------------|-------------|
| perfect delivery          | 60%         |
| delayed shipment          | 25%         |
| partial receipt           | 10%         |
| cancelled/short shipment  | 3%          |
| overdelivery              | 2%          |



# Shipments Table

Table: `shipments`

| Column          | Type    |
|-----------------|---------|
| `shipment_id`   | string  |
| `supplier_id`   | string  |
| `dispatch_date` | date    |
| `eta`           | date    |
| `actual_arrival`| date    |
| `transport_mode`| string  |
| `shipment_status`| string |
| `delay_reason`  | string  |

## Business Meaning

| Column          | Meaning                  |
|-----------------|--------------------------|
| `shipment_id`   | unique logistics event  |
| `supplier_id`   | source supplier         |
| `dispatch_date` | actual goods dispatch   |
| `eta`           | planned arrival         |
| `actual_arrival`| actual arrival          |
| `transport_mode`| air/sea/road/rail       |
| `shipment_status`| operational state      |
| `delay_reason`  | disruption metadata     |



## Realistic Business Rules

### Rule A: Shipment depends on PO delivery timing

`dispatch_date >= order_date`

Usually:

`dispatch_date = order_date + manufacturing/prep time`

Example:

- electronics supplier: 10–25 days prep
- packaging supplier: 2–7 days prep

### Rule B: ETA depends on geography + transport mode

Example realistic transit times:

| Mode | Domestic | International |
|------|----------|----------------|
| air  | 1–5 days | 3–10 days     |
| sea  | N/A      | 20–60 days    |
| road | 1–10 days| 5–15 days     |
| rail | 3–15 days| 10–25 days    |

### Rule C: Transport mode depends on category + urgency

Realistic patterns:

| Category    | Common Modes |
|-------------|--------------|
| electronics | air, sea     |
| metals      | sea, rail    |
| packaging   | road         |
| chemicals   | road, sea    |
| textiles    | sea, air     |

High-value electronics often use air freight.

Cheap heavy metal parts rarely do because air shipping steel is financially unwell behavior.

### Rule D: Shipment status depends on dates

Example logic:

| Condition                  | Status     |
|----------------------------|------------|
| actual_arrival null        | In Transit |
| actual_arrival <= eta      | Delivered  |
| actual_arrival > eta       | Delayed    |
| cancelled shipment         | Cancelled  |

### Rule E: Delay reason should NOT always exist


`delay_reason` populated ONLY if delayed.



## Enterprise Delay Modeling

Different suppliers exhibit different logistics reliability.

Example supplier profiles:

| Supplier Type          | Delay Risk    |
|------------------------|---------------|
| domestic packaging     | low           |
| overseas electronics   | medium/high   |
| port-dependent metals  | high          |

### 1. Recommended Delay Reasons (Weighted)

The following delay reasons are sampled according to realistic probabilities for different transport contexts.

| Delay Reason             | Typical Context       | Weight (Probability) |
|--------------------------|-----------------------|----------------------|
| Port Congestion          | sea freight           | 25%                  |
| Customs Clearance        | international         | 20%                  |
| Weather Disruption       | air / sea             | 10%                  |
| Supplier Production Delay| all                   | 15%                  |
| Documentation Issue      | international         | 10%                  |
| Carrier Capacity Shortage| air                   | 8%                   |
| Labor Strike             | port / rail           | 5%                   |
| None (on‑time)           | all                   | 7%                   |

> **Note:** Weights are illustrative. For production, adjust based on historical data or route-specific patterns.

### 2. Shipment Status Distribution

Assign shipment status using the following realistic probabilities:

| Status       | Probability |
|--------------|-------------|
| Delivered    | 70%         |
| Delayed      | 20%         |
| In Transit   | 7%          |
| Cancelled    | 3%          |

> **Generation rule:** If `Delayed` is selected, a delay reason must be sampled from the weighted table above.  
> If `Delivered` or `In Transit` and not delayed, use `None` as delay reason.

### 3. Geography Intelligence

Use the existing `country` and `city` fields to infer transport mode and risk profile.

#### Domestic Shipment Example (e.g., India → India)

- **Likely transport:** Road
- **Expected transit time:** Shorter (1–5 days)
- **Customs delays:** Rare
- **Dominant delay reasons:** Supplier production, carrier capacity

#### International Shipment Example (e.g., China → India)

- **Likely transport:** Sea (dominant) or air for urgent goods
- **Expected transit time:** Longer (15–40 days)
- **Customs risk:** High – documentation and clearance delays common
- **Port congestion:** Possible at major hubs (e.g., Mundra, Nhava Sheva)
- **Dominant delay reasons:** Port congestion, customs clearance, documentation issues

# Quality Inspection Table

| Column            | Type     | Description                                        |
|-------------------|----------|----------------------------------------------------|
| inspection_id     | string   | Unique identifier (e.g., `INSP-YYYYMMDD-XXXX`)     |
| supplier_id       | string   | Foreign key to suppliers table                     |
| inspection_date   | date     | Date when inspection occurred                      |
| inspected_units   | int      | Number of units sampled / inspected                |
| rejected_units    | int      | Number of units failing quality check              |
| defect_type       | string   | Primary defect category (see Section 2)            |
| severity          | string   | Critical / Major / Minor                           |

## 1. Enterprise Relationship Model
- `supplier_master` → `purchase_orders` → `shipments` → `quality_inspections`
- For synthetic modeling: **1 shipment → 1 inspection** (acceptable initially)

## 2. Enterprise Business Logic
- Inspections happen **AFTER receipt** → `inspection_date >= actual_arrival`
- No inspection for:
  - Shipments still in transit
  - Cancelled shipments

## 3. Core Enterprise Rules

### Rule A: Inspection only for delivered shipments
Do NOT generate inspections for cancelled or in-transit shipments.

### Rule B: Inspected units tied to PO receipt quantity
`inspected_units <= received_quantity`

| Supplier Criticality | Inspection Coverage |
|----------------------|---------------------|
| low                  | 5–20% sample        |
| medium               | 20–50%              |
| high-risk supplier   | 100%                |

### Rule C: Rejected units correlated to supplier quality
Each supplier has a `base_defect_rate`:

| Supplier Profile   | Defect Rate |
|--------------------|-------------|
| premium domestic   | 0.5%        |
| average global     | 2–5%        |
| unstable supplier  | 8–15%       |

## 4. Defect Type Must Match Category

| Category     | Defect Types                                      |
|--------------|---------------------------------------------------|
| Electronics  | Solder Failure, PCB Damage, Component Misalignment, ESD Damage |
| Metals       | Surface Corrosion, Dimensional Variance, Cracks, Material Impurity |
| Packaging    | Print Misalignment, Seal Failure, Compression Damage |

## 5. Severity Logic

| Rejection % | Severity    |
|-------------|-------------|
| <1%         | Low         |
| 1–5%        | Medium      |
| 5–10%       | High        |
| >10%        | Critical    |

*Safety-related defects or electronics failures may escalate severity automatically.*

## 6. Relationship with Shipment Delays
Delayed shipments → higher defect probability (rushed manufacturing, poor handling, etc.)

## 7. Enterprise Inspection Scenarios

| Scenario                   | Probability |
|----------------------------|-------------|
| clean inspection           | 65%         |
| minor defects              | 20%         |
| moderate rejection         | 10%         |
| severe quality failure     | 4%          |
| catastrophic batch rejection | 1%        |



# Inventory Table

| Column                  | Type   | Description                                         |
|-------------------------|--------|-----------------------------------------------------|
| component_id            | string | Unique component identifier                         |
| supplier_id             | string | Foreign key to supplier_master                      |
| current_stock           | float  | On-hand inventory quantity (units or kg)            |
| avg_daily_consumption   | float  | Average units consumed per day                      |
| safety_stock            | float  | Buffer stock to cover demand variability            |
| plant_id                | string | Foreign key to manufacturing plant                  |


## 1. Enterprise Relationship Model
- `supplier_master` → `purchase_orders` → `shipments` → `quality_inspections` → `inventory_status`
- Inventory is downstream operational state.

## 2. Business Meaning of Columns

| Column                  | Meaning                       |
|-------------------------|-------------------------------|
| component_id            | stocked component             |
| supplier_id             | supplying vendor              |
| current_stock           | usable inventory              |
| avg_daily_consumption   | plant usage rate              |
| safety_stock            | risk buffer                   |
| plant_id                | inventory location            |

## 3. Enterprise Inventory Logic
- **Correct operational formula:**  
  `current_stock = received_quantity - rejected_units - simulated consumption`
- This creates believable inventory dynamics.

## 4. Critical Business Rules

### Rule A: Inventory must inherit component lineage
- `component_id` must originate from PO. Never randomize inventory components independently.

### Rule B: Only usable inventory enters stock
- Rejected units reduce inventory.  
  `usable_inventory = received_quantity - rejected_units`

### Rule C: Consumption must depend on component category

| Category     | Consumption Pattern |
|--------------|---------------------|
| electronics  | moderate/high       |
| packaging    | very high           |
| metals       | medium              |
| chemicals    | variable            |

### Rule D: Safety stock depends on supply risk
- Real enterprises compute safety stock from lead time, demand volatility, supplier reliability.
- Synthetic approximation:  
  `safety_stock = avg_daily_consumption × lead_time_factor × risk_multiplier`

## 5. Plant Modeling
- Add realistic plants.

| Plant ID        | Specialization |
|-----------------|----------------|
| PLANT_IND_001   | electronics    |
| PLANT_IND_002   | packaging      |
| PLANT_US_001    | automotive     |

- Plants should consume compatible components.

## 6. Inventory Generation Strategy

### Step 1
Aggregate usable receipts: PO receipts − quality rejects

### Step 2
Simulate consumption: daily usage × elapsed days

### Step 3
Compute stock: remaining inventory

### Step 4
Generate safety stock based on criticality, supplier geography, delay risk

## 7. Enterprise Inventory Characteristics
- Real inventory should contain operational variety.

| Scenario            | Expected |
|---------------------|----------|
| healthy stock       | most     |
| near safety threshold | some  |
| stockout risk       | few      |
| excess stock        | few      |

## 8. Enterprise‑grade Plant Assignment Example


plant_map = {
    "electronics": ["PLANT_IND_001", "PLANT_IND_002"],
    "metals": ["PLANT_US_001"],
    "packaging": ["PLANT_IND_003"]
}


# Supplier Audit Table
# Table: supplier_audits

| Column              | Type   |
|---------------------|--------|
| audit_id            | string |
| supplier_id         | string |
| audit_date          | date   |
| audit_score         | float  |
| major_findings      | int    |
| minor_findings      | int    |
| compliance_status   | string |



## 1. Enterprise Relationship Model
- `supplier_master` → `purchase_orders` → `shipments` → `quality_inspections` → `inventory_status` → `supplier_audits`
- Audits summarize operational risk over time.

## 2. Business Meaning of Columns

| Column              | Meaning                         |
|---------------------|---------------------------------|
| audit_id            | unique audit event              |
| supplier_id         | audited supplier                |
| audit_date          | audit execution date            |
| audit_score         | operational/compliance score    |
| major_findings      | severe issues                   |
| minor_findings      | smaller issues                  |
| compliance_status   | audit outcome                   |

## 3. Enterprise Audit Logic
Audit outcomes should depend on supplier behavior. That’s the core principle.

## 4. What Should Influence Audits?

### A. Shipment performance
- Delayed shipments increase audit risk.  
  Example: high delay rate → lower audit score

### B. Quality performance
- High rejection rates should worsen audits.  
  Example: high defects → more findings

### C. Inventory instability
- Frequent low-stock situations suggest poor supplier reliability / supply instability. Should influence audit scores.

### D. Supplier criticality
- Critical suppliers: audited more often, held to stricter standards.

## 5. Enterprise Audit Scoring Model
Start from baseline: `audit_score = 100`

Apply penalties:

| Issue                     | Penalty      |
|---------------------------|--------------|
| delayed shipments         | -5 to -20    |
| critical defects          | -10 to -30   |
| high rejection rate       | -5 to -25    |
| stock instability         | -5 to -15    |
| poor compliance history   | -10          |

## 6. Compliance Status Logic

| Score     | Status         |
|-----------|----------------|
| 90+       | Compliant      |
| 75–89     | Conditional    |
| 60–74     | Under Review   |
| <60       | Non-Compliant  |

## 7. Major vs Minor Findings

### Minor Findings (examples)
- documentation gaps
- labeling issues
- delayed reporting

### Major Findings (examples)
- severe quality failures
- repeated shipment delays
- compliance violations
- unsafe material handling

## 8. Audit Frequency Logic
Not every supplier audited equally.

| Supplier Type     | Frequency          |
|-------------------|--------------------|
| critical suppliers| quarterly          |
| medium suppliers  | biannual           |
| low-risk suppliers| annual             |

Synthetic simplification: 1–4 audits per supplier/year, weighted by criticality.

# Supplier Incidents Table

| Column                     | Type   |
|----------------------------|--------|
| incident_id                | string |
| supplier_id                | string |
| incident_date              | date   |
| incident_type              | string |
| severity                   | string |
| operational_impact_hours   | float  |


## 1. Enterprise Relationship Model
- `supplier_master` → `purchase_orders` → `shipments` → `quality_inspections` → `inventory_status` → `supplier_audits` → `supplier_incidents`
- Incidents are escalation events.

## 2. Business Meaning of Columns

| Column                     | Meaning                               |
|----------------------------|---------------------------------------|
| incident_id                | unique disruption event               |
| supplier_id                | impacted supplier                     |
| incident_date              | event occurrence                      |
| incident_type              | operational failure category          |
| severity                   | business impact severity              |
| operational_impact_hours   | downtime / disruption duration        |

## 3. Enterprise Incident Logic
- Incidents should NOT occur uniformly. Risky suppliers naturally create more incidents.

## 4. What Should Drive Incidents?

### A. Shipment instability (high delay suppliers)
- port congestion, customs failure, logistics breakdowns

### B. Quality instability (high defects)
- rejected lots, production stoppages, recalls

### C. Inventory instability (low stock situations)
- plant downtime, line stoppages, emergency procurement

### D. Poor audits (non-compliant suppliers)
- regulatory issues, safety violations, supplier shutdowns

## 5. Incident Types

| Category          | Types                                                       |
|-------------------|-------------------------------------------------------------|
| Logistics-related | Shipment Delay, Port Congestion, Customs Hold, Carrier Failure |
| Quality-related   | Quality Failure, Batch Rejection, Product Recall            |
| Compliance-related| Audit Non-Compliance, Regulatory Violation                  |
| Inventory-related | Stockout, Supply Shortage                                   |
| Operational       | Production Shutdown, Labor Strike, Cybersecurity Incident  |

## 6. Severity Logic

| Severity | Meaning                            |
|----------|------------------------------------|
| Low      | minor operational issue            |
| Medium   | moderate disruption                |
| High     | severe operational impact          |
| Critical | major production / business risk   |

## 7. Impact Hours Logic

| Severity | Typical Impact |
|----------|----------------|
| Low      | 1–8 hrs        |
| Medium   | 8–24 hrs       |
| High     | 24–72 hrs      |
| Critical | 72–240 hrs     |

## 8. Enterprise Incident Frequency
- Most suppliers: few or no incidents
- Some suppliers: repeated operational failures (skew expected)

| Supplier Profile | Incidents per year |
|------------------|--------------------|
| excellent        | 0–1                |
| average          | 1–3                |
| poor             | 5–10               |