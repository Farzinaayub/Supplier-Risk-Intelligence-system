import pandas as pd
import numpy as np
import random
import yaml

from datetime import timedelta


# =========================================================
# LOAD CONFIG
# =========================================================

with open("config/supplier_audit_config.yaml", "r") as f:
    config = yaml.safe_load(f)


# =========================================================
# LOAD SOURCE TABLES
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


# =========================================================
# CONFIG SHORTCUTS
# =========================================================

audit_frequency = config[
    "audit_frequency_by_criticality"
]

penalties = config["penalties"]

international_risk = config[
    "international_risk"
]

audit_variance = config[
    "audit_variance"
]

audit_score_cfg = config[
    "audit_score"
]

major_findings_cfg = config[
    "major_findings"
]

minor_findings_cfg = config[
    "minor_findings"
]

compliance_rules = config[
    "compliance_rules"
]

audit_date_cfg = config[
    "audit_date"
]


# =========================================================
# BUILD SUPPLIER PERFORMANCE METRICS
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


# =========================================================
# MERGE SUPPLIER RISK PROFILE
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

)

supplier_risk = supplier_risk.fillna(0)


# =========================================================
# GENERATE AUDITS
# =========================================================

audit_rows = []

audit_counter = 1


for _, supplier in supplier_risk.iterrows():

    supplier_id = supplier["supplier_id"]

    criticality = supplier[
        "criticality_level"
    ]

    audit_count = audit_frequency[
        criticality
    ]


    for _ in range(audit_count):

        # -------------------------------------------------
        # BASE SCORE
        # -------------------------------------------------

        audit_score = 100


        # -------------------------------------------------
        # DELAY PENALTY
        # -------------------------------------------------

        audit_score -= (

            supplier["delay_ratio"]

            *

            penalties[
                "shipment_delay_multiplier"
            ]

        )


        # -------------------------------------------------
        # QUALITY PENALTY
        # -------------------------------------------------

        audit_score -= (

            supplier["rejection_ratio"]

            *

            penalties[
                "rejection_ratio_multiplier"
            ]

        )


        # -------------------------------------------------
        # INVENTORY RISK PENALTY
        # -------------------------------------------------

        audit_score -= (

            supplier["low_stock_ratio"]

            *

            penalties[
                "low_stock_multiplier"
            ]

        )


        # -------------------------------------------------
        # INTERNATIONAL RISK
        # -------------------------------------------------

        if (

            supplier["country"]

            !=

            international_risk[
                "domestic_country"
            ]

        ):

            audit_score -= np.random.uniform(

                international_risk[
                    "penalty_min"
                ],

                international_risk[
                    "penalty_max"
                ]

            )


        # -------------------------------------------------
        # RANDOM AUDIT VARIANCE
        # -------------------------------------------------

        audit_score += np.random.normal(

            audit_variance["mean"],

            audit_variance["stddev"]

        )


        # -------------------------------------------------
        # LIMIT SCORE
        # -------------------------------------------------

        audit_score = max(

            min(

                round(audit_score, 2),

                audit_score_cfg[
                    "max_score"
                ]

            ),

            audit_score_cfg[
                "min_score"
            ]

        )


        # -------------------------------------------------
        # MAJOR FINDINGS
        # -------------------------------------------------

        major_findings = 0


        if audit_score < 85:

            major_findings += np.random.randint(

                major_findings_cfg[
                    "audit_score_below_85"
                ]["min"],

                major_findings_cfg[
                    "audit_score_below_85"
                ]["max"] + 1

            )


        if audit_score < 70:

            major_findings += np.random.randint(

                major_findings_cfg[
                    "audit_score_below_70"
                ]["min"],

                major_findings_cfg[
                    "audit_score_below_70"
                ]["max"] + 1

            )


        if (

            supplier["rejection_ratio"]

            >

            major_findings_cfg[
                "rejection_ratio_threshold"
            ]

        ):

            major_findings += (

                major_findings_cfg[
                    "rejection_ratio_penalty"
                ]

            )


        # -------------------------------------------------
        # MINOR FINDINGS
        # -------------------------------------------------

        minor_findings = np.random.randint(

            minor_findings_cfg[
                "base_min"
            ],

            minor_findings_cfg[
                "base_max"
            ] + 1

        )


        if (

            supplier["delay_ratio"]

            >

            minor_findings_cfg[
                "delay_ratio_threshold"
            ]

        ):

            minor_findings += np.random.randint(

                minor_findings_cfg[
                    "additional_if_delayed"
                ]["min"],

                minor_findings_cfg[
                    "additional_if_delayed"
                ]["max"] + 1

            )


        # -------------------------------------------------
        # COMPLIANCE STATUS
        # -------------------------------------------------

        if (

            audit_score

            >=

            compliance_rules[
                "compliant_min"
            ]

        ):

            compliance_status = "Compliant"


        elif (

            audit_score

            >=

            compliance_rules[
                "conditional_min"
            ]

        ):

            compliance_status = "Conditional"


        elif (

            audit_score

            >=

            compliance_rules[
                "under_review_min"
            ]

        ):

            compliance_status = "Under Review"


        else:

            compliance_status = "Non-Compliant"


        # -------------------------------------------------
        # AUDIT DATE
        # -------------------------------------------------

        audit_date = (

            pd.Timestamp(
                audit_date_cfg[
                    "start_date"
                ]
            )

            +

            timedelta(

                days=np.random.randint(

                    0,

                    audit_date_cfg[
                        "random_days_range"
                    ]

                )

            )

        )


        # -------------------------------------------------
        # CREATE RECORD
        # -------------------------------------------------

        audit_rows.append({

            "audit_id":
                f"AUD{audit_counter:07}",

            "supplier_id":
                supplier_id,

            "audit_date":
                audit_date.date(),

            "audit_score":
                audit_score,

            "major_findings":
                major_findings,

            "minor_findings":
                minor_findings,

            "compliance_status":
                compliance_status
        })

        audit_counter += 1


# =========================================================
# FINAL TABLE
# =========================================================

df_supplier_audits = pd.DataFrame(
    audit_rows
)


# =========================================================
# VALIDATIONS
# =========================================================

print("\n==============================")
print("AUDIT SUMMARY")
print("==============================")

print(
    f"Total Audits: "
    f"{len(df_supplier_audits)}"
)

print("\nCompliance Distribution:")

print(
    df_supplier_audits[
        "compliance_status"
    ].value_counts()
)

print("\nAudit Score Summary:")

print(
    df_supplier_audits[
        "audit_score"
    ].describe()
)

print("\nSample Records:\n")

print(
    df_supplier_audits.head()
)


# =========================================================
# EXPORT
# =========================================================

df_supplier_audits.to_csv(

    config["dataset"]["output_path"],

    index=False

)