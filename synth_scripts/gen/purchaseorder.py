import pandas as pd
import numpy as np
import random
import yaml

from datetime import timedelta


# =========================================================
# LOAD CONFIG
# =========================================================

with open(
    "config/purchase_order_config.yaml",
    "r"
) as f:

    config = yaml.safe_load(f)


# =========================================================
# LOAD DATA
# =========================================================

df_suppliers = pd.read_csv(
    config["source_tables"]["suppliers"]
)


# =========================================================
# CONFIG SHORTCUTS
# =========================================================

n_po = config["dataset"]["n_rows"]

component_map = config["component_map"]

unit_prices = config["unit_prices"]

lead_times_cfg = config["lead_times"]

delivery_delay_cfg = config[
    "delivery_delay"
]

quantity_cfg = config[
    "quantity_distribution"
]

partial_delivery_cfg = config[
    "partial_delivery"
]


# =========================================================
# SUPPLIER WEIGHTS
# =========================================================

supplier_weights = (

    df_suppliers["contract_value"]

    /

    df_suppliers["contract_value"].sum()

)


# =========================================================
# PURCHASE ORDER GENERATION
# =========================================================

rows = []


for i in range(n_po):

    # =====================================================
    # SELECT SUPPLIER
    # =====================================================

    supplier = df_suppliers.sample(

        1,

        weights=supplier_weights

    ).iloc[0]


    category = supplier[
        "supplier_category"
    ]


    # =====================================================
    # COMPONENT SELECTION
    # =====================================================

    component = random.choice(

        component_map[category]

    )


    # =====================================================
    # ORDER DATE
    # =====================================================

    order_date = (

        pd.Timestamp(

            config["order_dates"][
                "start_date"
            ]

        )

        +

        pd.to_timedelta(

            np.random.randint(

                0,

                config["order_dates"][
                    "random_days_range"
                ]

            ),

            unit="D"

        )

    )


    # =====================================================
    # LEAD TIME
    # =====================================================

    lead_time_rule = lead_times_cfg.get(

        category,

        lead_times_cfg["default"]

    )


    lead_time = np.random.randint(

        lead_time_rule["min"],

        lead_time_rule["max"] + 1

    )


    expected_delivery = (

        order_date

        +

        timedelta(days=lead_time)

    )


    # =====================================================
    # DELIVERY DELAY
    # =====================================================

    delay = np.random.choice(

        delivery_delay_cfg["values"],

        p=delivery_delay_cfg[
            "probabilities"
        ]

    )


    actual_delivery = (

        expected_delivery

        +

        timedelta(days=int(delay))

    )


    # =====================================================
    # ORDER QUANTITY
    # =====================================================

    quantity = max(

        quantity_cfg["minimum_quantity"],

        int(

            np.random.lognormal(

                mean=quantity_cfg["mean"],

                sigma=quantity_cfg["sigma"]

            )

        )

    )


    # =====================================================
    # RECEIVED QUANTITY
    # =====================================================

    received = quantity

    partial_prob = np.random.rand()


    if (

        partial_prob

        <

        partial_delivery_cfg[
            "probability_threshold"
        ]

    ):

        received = int(

            quantity

            *

            np.random.uniform(

                partial_delivery_cfg[
                    "received_ratio"
                ]["min"],

                partial_delivery_cfg[
                    "received_ratio"
                ]["max"]

            )

        )


    # =====================================================
    # ORDER VALUE
    # =====================================================

    unit_price = unit_prices[
        component
    ]

    order_value = round(

        quantity * unit_price,

        2

    )


    # =====================================================
    # CREATE RECORD
    # =====================================================

    rows.append({

        "po_id":
            f"PO{i+1:07}",

        "supplier_id":
            supplier["supplier_id"],

        "order_date":
            order_date.date(),

        "expected_delivery_date":
            expected_delivery.date(),

        "actual_delivery_date":
            actual_delivery.date(),

        "order_quantity":
            quantity,

        "received_quantity":
            received,

        "order_value":
            order_value,

        "component_id":
            component
    })


# =========================================================
# FINAL DATAFRAME
# =========================================================

df_po = pd.DataFrame(rows)


# =========================================================
# VALIDATION OUTPUT
# =========================================================

print("\n==============================")
print("PURCHASE ORDER SUMMARY")
print("==============================")

print(
    f"Total Purchase Orders: "
    f"{len(df_po)}"
)

print("\nSample Records:\n")

print(
    df_po.head()
)

print("\nDataFrame Info:\n")

df_po.info()


# =========================================================
# EXPORT
# =========================================================

df_po.to_csv(

    config["dataset"]["output_path"],

    index=False

)