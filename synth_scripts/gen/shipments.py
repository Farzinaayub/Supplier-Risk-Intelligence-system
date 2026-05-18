import pandas as pd
import numpy as np
import random
import yaml

from datetime import timedelta


# =========================================================
# LOAD CONFIG
# =========================================================

with open(
    "config/shipment_generation_config.yaml",
    "r"
) as f:

    config = yaml.safe_load(f)


# =========================================================
# LOAD DATA
# =========================================================

df_suppliers = pd.read_csv(
    config["source_tables"]["suppliers"]
)

df_po = pd.read_csv(
    config["source_tables"]["purchase_orders"]
)


# =========================================================
# CONFIG SHORTCUTS
# =========================================================

delay_reasons = config["delay_reasons"]

transport_rules = config["transport_rules"]

prep_days_cfg = config["prep_days"]

transit_days_cfg = config["transit_days"]

domestic_rules = config["domestic_rules"]

criticality_rules = config[
    "criticality_rules"
]

shipment_status_cfg = config[
    "shipment_status_distribution"
]

delivery_variance_cfg = config[
    "delivery_variance"
]


# =========================================================
# SHIPMENT GENERATION
# =========================================================

shipment_rows = []

shipment_counter = 1


for _, po in df_po.iterrows():

    # =====================================================
    # GET SUPPLIER
    # =====================================================

    supplier = df_suppliers[

        df_suppliers["supplier_id"]

        ==

        po["supplier_id"]

    ].iloc[0]


    supplier_id = supplier["supplier_id"]

    category = supplier["supplier_category"]

    country = supplier["country"]

    criticality = supplier[
        "criticality_level"
    ]


    # =====================================================
    # PREPARATION DAYS
    # =====================================================

    prep_rule = prep_days_cfg.get(
        category,
        prep_days_cfg["default"]
    )

    prep_days = np.random.randint(

        prep_rule["min"],

        prep_rule["max"] + 1

    )


    # =====================================================
    # DISPATCH DATE
    # =====================================================

    dispatch_date = (

        pd.to_datetime(po["order_date"])

        +

        timedelta(days=int(prep_days))

    )


    # =====================================================
    # TRANSPORT MODE
    # =====================================================

    if category in transport_rules:

        transport_mode = np.random.choice(

            transport_rules[category]["modes"],

            p=transport_rules[category]["weights"]

        )

    else:

        transport_mode = "road"


    # =====================================================
    # INTERNATIONAL FLAG
    # =====================================================

    international = (

        country

        !=

        domestic_rules["domestic_country"]

    )


    # =====================================================
    # TRANSIT TIME
    # =====================================================

    transit_rule = transit_days_cfg[
        transport_mode
    ]

    transit_days = np.random.randint(

        transit_rule["min"],

        transit_rule["max"] + 1

    )


    # Domestic shipments faster
    if not international:

        transit_days *= domestic_rules[
            "domestic_speed_multiplier"
        ]


    # Expedited handling
    if (

        criticality

        >=

        criticality_rules[
            "expedited_threshold"
        ]

    ):

        transit_days *= criticality_rules[
            "expedited_multiplier"
        ]


    transit_days = max(
        1,
        int(transit_days)
    )


    # =====================================================
    # ETA
    # =====================================================

    eta = (

        dispatch_date

        +

        timedelta(days=transit_days)

    )


    # =====================================================
    # SHIPMENT STATUS
    # =====================================================

    status = np.random.choice(

        shipment_status_cfg["statuses"],

        p=shipment_status_cfg[
            "probabilities"
        ]

    )


    # =====================================================
    # ARRIVAL + DELAYS
    # =====================================================

    actual_arrival = None

    delay_reason = None


    if status == "Delivered":

        arrival_variance = np.random.randint(

            delivery_variance_cfg[
                "delivered"
            ]["min"],

            delivery_variance_cfg[
                "delivered"
            ]["max"] + 1

        )

        actual_arrival = (

            eta

            +

            timedelta(days=arrival_variance)

        )


    elif status == "Delayed":

        delay_days = np.random.randint(

            delivery_variance_cfg[
                "delayed"
            ]["min"],

            delivery_variance_cfg[
                "delayed"
            ]["max"] + 1

        )

        actual_arrival = (

            eta

            +

            timedelta(days=delay_days)

        )

        delay_reason = random.choice(
            delay_reasons
        )


    elif status == "In Transit":

        actual_arrival = None


    elif status == "Cancelled":

        actual_arrival = None

        delay_reason = config[
            "cancelled_reason"
        ]


    # =====================================================
    # CREATE RECORD
    # =====================================================

    shipment_rows.append({

        "shipment_id":
            f"SHP{shipment_counter:07}",

        "po_id":
            po["po_id"],

        "supplier_id":
            supplier_id,

        "dispatch_date":
            dispatch_date.date(),

        "eta":
            eta.date(),

        "actual_arrival":
            (
                actual_arrival.date()
                if actual_arrival is not None
                else None
            ),

        "transport_mode":
            transport_mode,

        "shipment_status":
            status,

        "delay_reason":
            delay_reason
    })

    shipment_counter += 1


# =========================================================
# FINAL DATAFRAME
# =========================================================

df_shipments = pd.DataFrame(
    shipment_rows
)


# =========================================================
# DATA CORRECTION
# =========================================================

mask = (

    pd.to_datetime(

        df_shipments["actual_arrival"],
        errors="coerce"

    )

    <

    pd.to_datetime(

        df_shipments["dispatch_date"],
        errors="coerce"

    )

)

df_shipments.loc[
    mask,
    "actual_arrival"
] = df_shipments.loc[
    mask,
    "eta"
]


# =========================================================
# VALIDATION OUTPUT
# =========================================================

print("\n==============================")
print("SHIPMENT SUMMARY")
print("==============================")

print(
    f"Total Shipments: "
    f"{len(df_shipments)}"
)

print(
    "\nShipment Status Distribution:"
)

print(
    df_shipments[
        "shipment_status"
    ].value_counts()
)

print(
    "\nTransport Mode Distribution:"
)

print(
    df_shipments[
        "transport_mode"
    ].value_counts()
)

print("\nSample Records:\n")

print(
    df_shipments.head()
)

print("\nDataFrame Info:\n")

df_shipments.info()

print("\nColumns:\n")

print(df_shipments.columns)

print(
    "\nShipments with NaN actual_arrival:"
)

shipments_with_nan_arrival = (

    df_shipments[
        df_shipments[
            "actual_arrival"
        ].isna()
    ]

)

print(

    shipments_with_nan_arrival[
        "shipment_status"
    ].unique()

)


# =========================================================
# EXPORT
# =========================================================

df_shipments.to_csv(

    config["dataset"]["output_path"],

    index=False

)