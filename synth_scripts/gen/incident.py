import pandas as pd
import numpy as np
import random
import yaml

from datetime import timedelta


# =========================================================
# LOAD CONFIG
# =========================================================

with open(
    "config/supplier_incident_config.yaml",
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

df_inventory = pd.read_csv(
    config["source_tables"]["inventory"]
)

df_supplier_audits = pd.read_csv(
    config["source_tables"]["supplier_audits"]
)


# =========================================================
# CONFIG SHORTCUTS
# =========================================================

incident_probability_cfg = config[
    "incident_probability"
]

incident_types = config[
    "incident_types"
]

severity_distribution = config[
    "severity_distribution"
]

severity_adjustments = config[
    "severity_adjustments"
]

impact_ranges = config[
    "impact_ranges"
]


# =========================================================
# BUILD SUPPLIER RISK PROFILE
# =========================================================

shipment_metrics = (

    df_shipments

    .groupby("supplier_id")

    .agg(

        total_shipments=(
            "shipment_id",
            "count"
        ),

        delayed_shipments=(
            "shipment_status",
            lambda x:
                (x == "Delayed").sum()
        )

    )

    .reset_index()

)

shipment_metrics["delay_ratio"] = (

    shipment_metrics["delayed_shipments"]

    /

    shipment_metrics["total_shipments"]

)


quality_metrics = (

    df_quality_inspections

    .groupby("supplier_id")

    .agg(

        total_inspected=(
            "inspected_units",
            "sum"
        ),

        total_rejected=(
            "rejected_units",
            "sum"
        )

    )

    .reset_index()

)

quality_metrics["rejection_ratio"] = (

    quality_metrics["total_rejected"]

    /

    quality_metrics["total_inspected"]

)

quality_metrics["rejection_ratio"] = (

    quality_metrics["rejection_ratio"]

    .fillna(0)

)


inventory_metrics = (

    df_inventory

    .groupby("supplier_id")

    .apply(

        lambda x:

        (
            x["current_stock"]

            <

            x["safety_stock"]

        ).mean()

    )

    .reset_index(name="low_stock_ratio")

)


audit_metrics = (

    df_supplier_audits

    .groupby("supplier_id")

    .agg(

        avg_audit_score=(
            "audit_score",
            "mean"
        )

    )

    .reset_index()

)


# =========================================================
# MERGE RISK PROFILE
# =========================================================

supplier_risk = (

    df_suppliers[[
        "supplier_id",
        "criticality_level",
        "country"
    ]]

    .merge(
        shipment_metrics,
        on="supplier_id",
        how="left"
    )

    .merge(
        quality_metrics,
        on="supplier_id",
        how="left"
    )

    .merge(
        inventory_metrics,
        on="supplier_id",
        how="left"
    )

    .merge(
        audit_metrics,
        on="supplier_id",
        how="left"
    )

)

supplier_risk = supplier_risk.fillna(0)


# =========================================================
# GENERATE INCIDENTS
# =========================================================

incident_rows = []

incident_counter = 1


for _, supplier in supplier_risk.iterrows():

    supplier_id = supplier["supplier_id"]

    criticality = supplier[
        "criticality_level"
    ]


    # =====================================================
    # INCIDENT PROBABILITY
    # =====================================================

    incident_probability = (

        incident_probability_cfg[
            "base_probability"
        ]

    )


    incident_probability += (

        supplier["delay_ratio"]

        *

        incident_probability_cfg[
            "delay_ratio_multiplier"
        ]

    )


    incident_probability += (

        supplier["rejection_ratio"]

        *

        incident_probability_cfg[
            "rejection_ratio_multiplier"
        ]

    )


    incident_probability += (

        supplier["low_stock_ratio"]

        *

        incident_probability_cfg[
            "low_stock_ratio_multiplier"
        ]

    )


    if supplier["avg_audit_score"] < 70:

        incident_probability += (

            incident_probability_cfg[
                "audit_score"
            ]["below_70"]

        )

    elif supplier["avg_audit_score"] < 85:

        incident_probability += (

            incident_probability_cfg[
                "audit_score"
            ]["below_85"]

        )


    if criticality >= 4:

        incident_probability += (

            incident_probability_cfg[
                "high_criticality_increment"
            ]

        )


    incident_probability = min(

        incident_probability,

        incident_probability_cfg[
            "max_probability"
        ]

    )


    # =====================================================
    # INCIDENT COUNT
    # =====================================================

    incident_count = np.random.poisson(

        incident_probability

        *

        config["incident_count"][
            "poisson_multiplier"
        ]

    )


    for _ in range(incident_count):

        # =================================================
        # INCIDENT CATEGORY
        # =================================================

        risk_weights = {

            "logistics":
                supplier["delay_ratio"],

            "quality":
                supplier["rejection_ratio"],

            "inventory":
                supplier["low_stock_ratio"],

            "compliance":
                max(
                    0,
                    (
                        80
                        -
                        supplier[
                            "avg_audit_score"
                        ]
                    ) / 100
                ),

            "operations":
                0.10
        }


        total_weight = sum(
            risk_weights.values()
        )


        if total_weight == 0:

            incident_category = (
                "operations"
            )

        else:

            normalized_weights = [

                v / total_weight

                for v in risk_weights.values()

            ]


            incident_category = np.random.choice(

                list(risk_weights.keys()),

                p=normalized_weights

            )


        # =================================================
        # INCIDENT TYPE
        # =================================================

        incident_type = random.choice(

            incident_types[
                incident_category
            ]

        )


        # =================================================
        # SEVERITY
        # =================================================

        severity_weights = dict(
            severity_distribution
        )


        if supplier["avg_audit_score"] < 70:

            severity_weights[
                "Critical"
            ] += (

                severity_adjustments[
                    "audit_score_below_70"
                ]["Critical"]

            )

            severity_weights[
                "High"
            ] += (

                severity_adjustments[
                    "audit_score_below_70"
                ]["High"]

            )


        severity = np.random.choice(

            list(severity_weights.keys()),

            p=np.array(
                list(severity_weights.values())
            )

            /

            sum(severity_weights.values())

        )


        # =================================================
        # OPERATIONAL IMPACT
        # =================================================

        low = impact_ranges[
            severity
        ]["min"]

        high = impact_ranges[
            severity
        ]["max"]


        operational_impact_hours = round(

            np.random.uniform(low, high),

            2

        )


        # =================================================
        # INCIDENT DATE
        # =================================================

        incident_date = (

            pd.Timestamp(

                config["incident_dates"][
                    "start_date"
                ]

            )

            +

            timedelta(

                days=np.random.randint(

                    0,

                    config[
                        "incident_dates"
                    ][
                        "random_days_range"
                    ]

                )

            )

        )


        # =================================================
        # CREATE RECORD
        # =================================================

        incident_rows.append({

            "incident_id":
                f"INC{incident_counter:07}",

            "supplier_id":
                supplier_id,

            "incident_date":
                incident_date.date(),

            "incident_type":
                incident_type,

            "severity":
                severity,

            "operational_impact_hours":
                operational_impact_hours
        })

        incident_counter += 1


# =========================================================
# FINAL DATAFRAME
# =========================================================

df_supplier_incidents = pd.DataFrame(
    incident_rows
)


# =========================================================
# VALIDATIONS
# =========================================================

print("\n==============================")
print("INCIDENT SUMMARY")
print("==============================")

print(
    f"Total Incidents: "
    f"{len(df_supplier_incidents)}"
)

print("\nSeverity Distribution:")

print(
    df_supplier_incidents[
        "severity"
    ].value_counts()
)

print("\nIncident Types:")

print(
    df_supplier_incidents[
        "incident_type"
    ].value_counts()
)

print("\nImpact Hours Summary:")

print(
    df_supplier_incidents[
        "operational_impact_hours"
    ].describe()
)

print("\nSample Records:\n")

print(
    df_supplier_incidents.head()
)


# =========================================================
# EXPORT
# =========================================================

df_supplier_incidents.to_csv(

    config["dataset"]["output_path"],

    index=False

)