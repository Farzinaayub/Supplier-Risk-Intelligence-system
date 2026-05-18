import pandas as pd
import numpy as np
import random
import yaml


# =========================================================
# LOAD CONFIG
# =========================================================

with open(
    "config/inventory_config.yaml",
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

df_shipments = pd.read_csv(
    config["source_tables"]["shipments"]
)

df_quality_inspections = pd.read_csv(
    config["source_tables"]["quality_inspections"]
)


# =========================================================
# CONFIG SHORTCUTS
# =========================================================

plant_map = config["plant_map"]

consumption_ranges = config[
    "consumption_ranges"
]

safety_stock_cfg = config[
    "safety_stock"
]


# =========================================================
# MERGE QUALITY DATA
# =========================================================

quality_summary = (

    df_quality_inspections

    .groupby("po_id")["rejected_units"]

    .sum()

    .reset_index()

)


quality_summary.rename(

    columns={

        "rejected_units":
        "total_rejected_units"

    },

    inplace=True

)


# =========================================================
# MERGE INTO PO
# =========================================================

inventory_base = df_po.merge(

    quality_summary,

    on="po_id",

    how="left"

)


inventory_base[
    "total_rejected_units"
] = (

    inventory_base[
        "total_rejected_units"
    ]

    .fillna(0)

)


# =========================================================
# USABLE INVENTORY
# =========================================================

inventory_base["usable_inventory"] = (

    inventory_base["received_quantity"]

    -

    inventory_base[
        "total_rejected_units"
    ]

)


inventory_base["usable_inventory"] = (

    inventory_base["usable_inventory"]

    .clip(lower=0)

)


# =========================================================
# BUILD INVENTORY TABLE
# =========================================================

inventory_rows = []

inventory_counter = 1


for _, row in inventory_base.iterrows():

    supplier = df_suppliers[

        df_suppliers["supplier_id"]

        ==

        row["supplier_id"]

    ].iloc[0]


    category = supplier[
        "supplier_category"
    ]

    criticality = supplier[
        "criticality_level"
    ]

    country = supplier["country"]


    # =====================================================
    # PLANT ASSIGNMENT
    # =====================================================

    plant_id = random.choice(

        plant_map.get(

            category,

            plant_map["default"]

        )

    )


    # =====================================================
    # DAILY CONSUMPTION
    # =====================================================

    consumption_rule = (

        consumption_ranges.get(

            category,

            consumption_ranges["default"]

        )

    )


    avg_daily_consumption = round(

        np.random.uniform(

            consumption_rule["min"],

            consumption_rule["max"]

        ),

        2

    )


    # =====================================================
    # SIMULATED CONSUMPTION PERIOD
    # =====================================================

    consumption_days = np.random.randint(

        config["consumption_days"]["min"],

        config["consumption_days"]["max"] + 1

    )


    # =====================================================
    # CONSUMED INVENTORY
    # =====================================================

    max_consumption_ratio = np.random.uniform(

        config["max_consumption_ratio"]["min"],

        config["max_consumption_ratio"]["max"]

    )


    consumed_inventory = (

        row["usable_inventory"]

        *

        max_consumption_ratio

    )


    # =====================================================
    # CURRENT STOCK
    # =====================================================

    current_stock = (

        row["usable_inventory"]

        -

        consumed_inventory

    )


    current_stock = max(

        round(current_stock, 2),

        0

    )


    # =====================================================
    # SAFETY STOCK
    # =====================================================

    safety_multiplier = (

        safety_stock_cfg[
            "base_multiplier"
        ]

    )


    if (

        country

        !=

        config["domestic_country"]

    ):

        safety_multiplier += (

            safety_stock_cfg[
                "international_supplier_increment"
            ]

        )


    if criticality >= 4:

        safety_multiplier += (

            safety_stock_cfg[
                "high_criticality_increment"
            ]

        )


    lead_time_days = np.random.randint(

        safety_stock_cfg[
            "lead_time_days"
        ]["min"],

        safety_stock_cfg[
            "lead_time_days"
        ]["max"] + 1

    )


    safety_stock = (

        avg_daily_consumption

        *

        lead_time_days

        *

        np.random.uniform(

            safety_stock_cfg[
                "variability_multiplier"
            ]["min"],

            safety_stock_cfg[
                "variability_multiplier"
            ]["max"]

        )

    )


    # =====================================================
    # CREATE RECORD
    # =====================================================

    inventory_rows.append({

        "inventory_id":
            f"INV{inventory_counter:07}",

        "component_id":
            row["component_id"],

        "supplier_id":
            row["supplier_id"],

        "current_stock":
            current_stock,

        "avg_daily_consumption":
            avg_daily_consumption,

        "safety_stock":
            safety_stock,

        "plant_id":
            plant_id
    })


    inventory_counter += 1


# =========================================================
# FINAL DATAFRAME
# =========================================================

df_inventory_status = pd.DataFrame(
    inventory_rows
)


# =========================================================
# VALIDATIONS
# =========================================================

print("\n==============================")
print("INVENTORY SUMMARY")
print("==============================")

print(
    f"Total Inventory Records: "
    f"{len(df_inventory_status)}"
)

print("\nLow Stock Situations:")

low_stock = df_inventory_status[

    df_inventory_status["current_stock"]

    <

    df_inventory_status["safety_stock"]

]

print(len(low_stock))


print("\nPlant Distribution:")

print(
    df_inventory_status[
        "plant_id"
    ].value_counts()
)

print("\nSample Records:\n")

print(
    df_inventory_status.head()
)


# =========================================================
# EXPORT
# =========================================================

df_inventory_status.to_csv(

    config["dataset"]["output_path"],

    index=False

)