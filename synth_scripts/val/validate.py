import pandas as pd
import numpy as np


# =========================================================
# HELPER FUNCTION
# =========================================================

def run_test(test_name, test_func):
    try:
        test_func()
    except Exception as e:
        print(f"❌ {test_name} FAILED")
        print(f"   ERROR: {e}\n")
    else:
        print(f"✅ {test_name} PASSED\n")


# =========================================================
# LOAD DATA
# =========================================================

df_suppliers = pd.read_csv("data/raw/df_suppliers.csv")
df_po = pd.read_csv("data/raw/df_purchase_orders.csv")
df_shipments = pd.read_csv("data/raw/df_shipments.csv")
df_quality = pd.read_csv("data/raw/df_quality_inspections.csv")
df_inventory = pd.read_csv("data/raw/df_inventory.csv")
df_supplier_audits = pd.read_csv("data/raw/df_supplier_audits.csv")
df_supplier_incidents = pd.read_csv("data/raw/df_supplier_incidents.csv")


print("\n===================================")
print("VALIDATION STARTED")
print("===================================\n")


# =========================================================
# STRUCTURAL TESTS
# =========================================================

def test_supplier_id_unique():
    assert df_suppliers["supplier_id"].is_unique, \
        "Duplicate supplier_id found"

run_test(
    "Supplier ID uniqueness",
    test_supplier_id_unique
)


def test_supplier_mandatory_columns():
    mandatory_cols = [
        "supplier_id",
        "supplier_category",
        "country"
    ]

    assert (
        df_suppliers[mandatory_cols]
        .isnull()
        .sum()
        .sum() == 0
    ), "Null values found in supplier mandatory columns"

run_test(
    "Supplier mandatory columns",
    test_supplier_mandatory_columns
)


def test_po_id_unique():
    assert df_po["po_id"].is_unique, \
        "Duplicate po_id found"

run_test(
    "PO ID uniqueness",
    test_po_id_unique
)


def test_po_supplier_fk():
    assert (
        df_po["supplier_id"]
        .isin(df_suppliers["supplier_id"])
        .all()
    ), "Invalid supplier_id in PO table"

run_test(
    "PO supplier FK validation",
    test_po_supplier_fk
)


def test_received_quantity():
    assert (
        df_po["received_quantity"]
        <= df_po["order_quantity"]
    ).all(), "Received quantity exceeds ordered quantity"

run_test(
    "Received quantity validation",
    test_received_quantity
)


def test_shipment_po_fk():
    assert (
        df_shipments["po_id"]
        .isin(df_po["po_id"])
        .all()
    ), "Shipment references invalid PO"

run_test(
    "Shipment PO FK validation",
    test_shipment_po_fk
)


def test_supplier_consistency():
    merged = df_shipments.merge(
        df_po[["po_id", "supplier_id"]],
        on="po_id",
        suffixes=("_ship", "_po")
    )

    assert (
        merged["supplier_id_ship"]
        == merged["supplier_id_po"]
    ).all(), "Supplier mismatch between shipment and PO"

run_test(
    "Shipment supplier consistency",
    test_supplier_consistency
)


def test_quality_fk():
    assert (
        df_quality["shipment_id"]
        .isin(df_shipments["shipment_id"])
        .all()
    ), "Quality table contains invalid shipment_id"

run_test(
    "Quality shipment FK validation",
    test_quality_fk
)


def test_rejected_units():
    assert (
        df_quality["rejected_units"]
        <= df_quality["inspected_units"]
    ).all(), "Rejected units exceed inspected units"

run_test(
    "Rejected units validation",
    test_rejected_units
)


# =========================================================
# TEMPORAL VALIDATION
# =========================================================

def test_expected_delivery_dates():
    assert (
        pd.to_datetime(df_po["expected_delivery_date"])
        >= pd.to_datetime(df_po["order_date"])
    ).all(), "Expected delivery before order date"

run_test(
    "Expected delivery date validation",
    test_expected_delivery_dates
)


def test_eta_dates():
    assert (
        pd.to_datetime(df_shipments["eta"])
        >= pd.to_datetime(df_shipments["dispatch_date"])
    ).all(), "ETA before dispatch date"

run_test(
    "Shipment ETA validation",
    test_eta_dates
)


def test_actual_arrival_dates():
    delivered = df_shipments[
        df_shipments["actual_arrival"].notnull()
    ]

    assert (
        pd.to_datetime(delivered["actual_arrival"])
        >= pd.to_datetime(delivered["dispatch_date"])
    ).all(), "Actual arrival before dispatch"

run_test(
    "Actual arrival validation",
    test_actual_arrival_dates
)


# =========================================================
# KPI VALIDATION
# =========================================================

def test_defect_rate():
    df_quality["defect_rate"] = (
        df_quality["rejected_units"]
        / df_quality["inspected_units"]
    )

    assert (
        df_quality["defect_rate"]
        .between(0, 1)
        .all()
    ), "Invalid defect rate detected"

run_test(
    "Defect rate validation",
    test_defect_rate
)


# =========================================================
# INVENTORY VALIDATION
# =========================================================

def test_inventory_uniqueness():
    assert (
        df_inventory["inventory_id"]
        .is_unique
    ), "Duplicate inventory_id found"

run_test(
    "Inventory ID uniqueness",
    test_inventory_uniqueness
)


def test_inventory_stock():
    assert (
        df_inventory["current_stock"] >= 0
    ).all(), "Negative inventory found"

run_test(
    "Inventory stock validation",
    test_inventory_stock
)


def test_inventory_consumption():
    assert (
        df_inventory["avg_daily_consumption"] > 0
    ).all(), "Invalid avg_daily_consumption found"

run_test(
    "Inventory consumption validation",
    test_inventory_consumption
)


# =========================================================
# AUDIT VALIDATION
# =========================================================

def test_audit_score_range():
    assert (
        (
            df_supplier_audits["audit_score"] >= 0
        )
        &
        (
            df_supplier_audits["audit_score"] <= 100
        )
    ).all(), "Audit score outside valid range"

run_test(
    "Audit score range validation",
    test_audit_score_range
)


def test_audit_supplier_fk():
    assert (
        df_supplier_audits["supplier_id"]
        .isin(df_suppliers["supplier_id"])
        .all()
    ), "Invalid supplier_id in audit table"

run_test(
    "Audit supplier FK validation",
    test_audit_supplier_fk
)


# =========================================================
# INCIDENT VALIDATION
# =========================================================

def test_incident_id_unique():
    assert (
        df_supplier_incidents["incident_id"]
        .is_unique
    ), "Duplicate incident_id found"

run_test(
    "Incident ID uniqueness",
    test_incident_id_unique
)


def test_incident_supplier_fk():
    assert (
        df_supplier_incidents["supplier_id"]
        .isin(df_suppliers["supplier_id"])
        .all()
    ), "Invalid supplier_id in incident table"

run_test(
    "Incident supplier FK validation",
    test_incident_supplier_fk
)


def test_incident_impact_hours():
    assert (
        df_supplier_incidents[
            "operational_impact_hours"
        ] > 0
    ).all(), "Invalid impact hours detected"

run_test(
    "Incident impact hours validation",
    test_incident_impact_hours
)


# =========================================================
# FINAL SUMMARY
# =========================================================

print("\n===================================")
print("VALIDATION EXECUTION COMPLETE")
print("===================================\n")