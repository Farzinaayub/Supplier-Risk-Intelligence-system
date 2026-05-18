import pandas as pd
import numpy as np
import random
import yaml

from datetime import timedelta


# =========================================================
# LOAD CONFIG
# =========================================================

with open(
    "config/quality_inspection_config.yaml",
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


# =========================================================
# CONFIG SHORTCUTS
# =========================================================

defect_map = config["defect_map"]

quality_profiles_cfg = config[
    "supplier_quality_profiles"
]

quality_defect_rates = config[
    "quality_defect_rates"
]

inspection_probability_cfg = config[
    "inspection_probability"
]

inspection_ratio_cfg = config[
    "inspection_ratio"
]

defect_rate_adjustments = config[
    "defect_rate_adjustments"
]

severity_thresholds = config[
    "severity_thresholds"
]


# =========================================================
# SUPPLIER QUALITY PROFILES
# =========================================================

supplier_quality_profiles = {}

for _, supplier in df_suppliers.iterrows():

    profile = np.random.choice(

        quality_profiles_cfg["profiles"],

        p=quality_profiles_cfg[
            "probabilities"
        ]

    )

    supplier_quality_profiles[
        supplier["supplier_id"]
    ] = profile


# =========================================================
# QUALITY INSPECTION GENERATION
# =========================================================

inspection_rows = []

inspection_counter = 1


for _, shipment in df_shipments.iterrows():

    # =====================================================
    # ONLY DELIVERED/DELAYED SHIPMENTS
    # =====================================================

    if shipment["shipment_status"] not in [
        "Delivered",
        "Delayed"
    ]:

        continue


    supplier_id = shipment["supplier_id"]


    # =====================================================
    # SUPPLIER RECORD
    # =====================================================

    supplier = df_suppliers[

        df_suppliers["supplier_id"]

        ==

        supplier_id

    ].iloc[0]


    supplier_category = supplier[
        "supplier_category"
    ]

    criticality = supplier[
        "criticality_level"
    ]

    supplier_country = supplier[
        "country"
    ]


    # =====================================================
    # LINKED PO
    # =====================================================

    po_id = shipment["po_id"]

    po = df_po[

        df_po["po_id"]

        ==

        po_id

    ].iloc[0]


    received_quantity = po[
        "received_quantity"
    ]

    order_value = po["order_value"]


    # =====================================================
    # QUALITY PROFILE
    # =====================================================

    quality_profile = (

        supplier_quality_profiles[
            supplier_id
        ]

    )

    base_defect_rate = (

        quality_defect_rates[
            quality_profile
        ]

    )


    # =====================================================
    # INSPECTION PROBABILITY
    # =====================================================

    inspection_probability = (

        inspection_probability_cfg[
            "base_probability"
        ]

    )


    if criticality >= 4:

        inspection_probability += (

            inspection_probability_cfg[
                "criticality"
            ]["level_4_plus"]

        )

    elif criticality == 3:

        inspection_probability += (

            inspection_probability_cfg[
                "criticality"
            ]["level_3"]

        )


    if shipment["shipment_status"] == "Delayed":

        inspection_probability += (

            inspection_probability_cfg[
                "delayed_shipment"
            ]

        )


    if quality_profile == "poor":

        inspection_probability += (

            inspection_probability_cfg[
                "supplier_quality"
            ]["poor"]

        )

    elif quality_profile == "average":

        inspection_probability += (

            inspection_probability_cfg[
                "supplier_quality"
            ]["average"]

        )

    elif quality_profile == "excellent":

        inspection_probability += (

            inspection_probability_cfg[
                "supplier_quality"
            ]["excellent"]

        )


    if (

        order_value

        >

        inspection_probability_cfg[
            "high_order_value"
        ]["threshold"]

    ):

        inspection_probability += (

            inspection_probability_cfg[
                "high_order_value"
            ]["increment"]

        )


    if (

        supplier_country

        !=

        config["domestic_country"]

    ):

        inspection_probability += (

            inspection_probability_cfg[
                "international_supplier"
            ]

        )


    inspection_probability = min(

        max(

            inspection_probability,

            inspection_probability_cfg[
                "min_probability"
            ]

        ),

        inspection_probability_cfg[
            "max_probability"
        ]

    )


    # =====================================================
    # SKIP SOME SHIPMENTS
    # =====================================================

    if np.random.rand() > inspection_probability:

        continue


    # =====================================================
    # INSPECTION DATE
    # =====================================================

    actual_arrival = pd.to_datetime(
        shipment["actual_arrival"]
    )

    inspection_date = (

        actual_arrival

        +

        timedelta(

            days=np.random.randint(

                config["inspection_date"][
                    "min_days_after_arrival"
                ],

                config["inspection_date"][
                    "max_days_after_arrival"
                ] + 1

            )

        )

    )


    # =====================================================
    # INSPECTED UNITS
    # =====================================================

    inspection_ratio = np.random.uniform(

        inspection_ratio_cfg[
            criticality
        ]["min"],

        inspection_ratio_cfg[
            criticality
        ]["max"]

    )


    inspected_units = int(
        received_quantity * inspection_ratio
    )

    inspected_units = max(
        inspected_units,
        1
    )


    # =====================================================
    # DEFECT RATE ADJUSTMENTS
    # =====================================================

    adjusted_defect_rate = (
        base_defect_rate
    )


    if shipment["shipment_status"] == "Delayed":

        adjusted_defect_rate *= (

            defect_rate_adjustments[
                "delayed_shipment_multiplier"
            ]

        )


    if shipment["transport_mode"] == "sea":

        adjusted_defect_rate *= (

            defect_rate_adjustments[
                "transport_mode"
            ]["sea"]

        )

    elif shipment["transport_mode"] == "air":

        adjusted_defect_rate *= (

            defect_rate_adjustments[
                "transport_mode"
            ]["air"]

        )


    if criticality >= 4:

        adjusted_defect_rate *= (

            defect_rate_adjustments[
                "high_criticality_multiplier"
            ]

        )


    adjusted_defect_rate *= np.random.uniform(

        defect_rate_adjustments[
            "operational_variance"
        ]["min"],

        defect_rate_adjustments[
            "operational_variance"
        ]["max"]

    )


    # =====================================================
    # REJECTED UNITS
    # =====================================================

    rejected_units = int(

        inspected_units

        *

        adjusted_defect_rate

    )


    rejected_units += np.random.randint(

        config[
            "rejected_units_randomness"
        ]["min"],

        max(

            config[
                "rejected_units_randomness"
            ]["fallback_max"],

            int(

                inspected_units

                *

                config[
                    "rejected_units_randomness"
                ]["multiplier"]

            )

        )

    )


    rejected_units = min(
        rejected_units,
        inspected_units
    )

    rejected_units = max(
        rejected_units,
        0
    )


    # =====================================================
    # DEFECT TYPE
    # =====================================================

    if rejected_units == 0:

        defect_type = "None"

    else:

        defect_type = random.choice(

            defect_map.get(

                supplier_category,

                ["General Defect"]

            )

        )


    # =====================================================
    # SEVERITY
    # =====================================================

    rejection_pct = (
        rejected_units / inspected_units
    )


    if rejected_units == 0:

        severity = "Low"

    elif rejection_pct < severity_thresholds["low"]:

        severity = "Low"

    elif rejection_pct < severity_thresholds["medium"]:

        severity = "Medium"

    elif rejection_pct < severity_thresholds["high"]:

        severity = "High"

    else:

        severity = "Critical"


    # Electronics escalation
    if (

        supplier_category == "electronics"

        and

        defect_type in config[
            "electronics_severe_defects"
        ]

        and rejected_units > 0

    ):

        severity = random.choice(

            config[
                "electronics_severity_override"
            ]

        )


    # =====================================================
    # CREATE RECORD
    # =====================================================

    inspection_rows.append({

        "inspection_id":
            f"INS{inspection_counter:07}",

        "shipment_id":
            shipment["shipment_id"],

        "po_id":
            po_id,

        "supplier_id":
            supplier_id,

        "inspection_date":
            inspection_date.date(),

        "inspected_units":
            inspected_units,

        "rejected_units":
            rejected_units,

        "defect_type":
            defect_type,

        "severity":
            severity
    })

    inspection_counter += 1


# =========================================================
# FINAL DATAFRAME
# =========================================================

df_quality_inspections = pd.DataFrame(
    inspection_rows
)


# =========================================================
# NULL DATE CORRECTION
# =========================================================

df_quality_inspections = (

    df_quality_inspections.merge(

        df_shipments[
            ["shipment_id", "actual_arrival"]
        ],

        on="shipment_id",

        how="left"

    )

)

df_quality_inspections.loc[

    df_quality_inspections[
        "actual_arrival"
    ].isna(),

    "inspection_date"

] = pd.NaT

df_quality_inspections.drop(

    columns=["actual_arrival"],

    inplace=True

)


# =========================================================
# VALIDATIONS
# =========================================================

print("\n==============================")
print("QUALITY INSPECTION SUMMARY")
print("==============================")

print(
    f"Total inspections: "
    f"{len(df_quality_inspections)}"
)

print("\nSeverity Distribution:")

print(
    df_quality_inspections[
        "severity"
    ].value_counts()
)

print("\nDefect Distribution:")

print(
    df_quality_inspections[
        "defect_type"
    ].value_counts().head(10)
)

print("\nInspection Coverage %:")

coverage = (

    len(df_quality_inspections)

    /

    len(df_shipments)

) * 100

print(round(coverage, 2), "%")

print("\nSample Records:\n")

print(
    df_quality_inspections.head()
)

print("\nDataFrame Info:\n")

df_quality_inspections.info()


problem_records = (

    df_quality_inspections

    .merge(

        df_shipments[
            ["shipment_id", "shipment_status"]
        ],

        on="shipment_id",

        how="left"

    )

    .loc[
        lambda df:
        ~df["shipment_status"].isin(
            ["Delivered", "Delayed"]
        )
    ]

)

print("\nProblem Records:\n")

print(problem_records)


unique_shipment_status = (

    df_quality_inspections

    .merge(

        df_shipments[
            ["shipment_id", "shipment_status"]
        ],

        on="shipment_id",

        how="left"

    )["shipment_status"]

    .dropna()

    .unique()

)

print("\nUnique Shipment Status:\n")

print(unique_shipment_status)


# =========================================================
# EXPORT
# =========================================================

df_quality_inspections.to_csv(

    config["dataset"]["output_path"],

    index=False

)