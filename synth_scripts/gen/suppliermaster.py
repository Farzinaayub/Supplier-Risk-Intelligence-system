
import pandas as pd
import numpy as np
import random
import yaml



# Load configuration

with open("config/supplier_master_config.yaml", "r") as f:
    config = yaml.safe_load(f)



# Core config

n = config["dataset"]["n_rows"]

categories = config["categories"]

country_city = config["country_city"]

criticality_values = config["criticality"]["values"]
criticality_probs = config["criticality"]["probabilities"]

payment_terms = config["payment_terms"]["values"]
payment_weights = config["payment_terms"]["probabilities"]

prefixes = config["supplier_name_generation"]["prefixes"]
industries = config["supplier_name_generation"]["industries"]
suffixes = config["supplier_name_generation"]["suffixes"]

onboarding_cfg = config["onboarding_time_days"]

contract_cfg = config["contract_value"]



rows = []

for i in range(n):

    # Supplier category
    category = np.random.choice(
        list(categories.keys()),
        p=list(categories.values())
    )

    # Geography
    country = random.choice(list(country_city.keys()))
    city = random.choice(country_city[country])

    # Criticality
    criticality = np.random.choice(
        criticality_values,
        p=criticality_probs
    )

    # Alternate supplier availability
    alternate = (
        np.random.rand() <
        (1 - criticality * 0.15)
    )

    # Onboarding time logic
    onboarding_rule = onboarding_cfg.get(
        category,
        onboarding_cfg["default"]
    )

    onboarding = np.random.randint(
        onboarding_rule["min"],
        onboarding_rule["max"] + 1
    )

    # Contract value
    contract_value = round(
        np.random.lognormal(
            mean=contract_cfg["mean"],
            sigma=contract_cfg["sigma"]
        ),
        2
    )

    # Payment terms
    payment = np.random.choice(
        payment_terms,
        p=payment_weights
    )

    # Supplier name generation
    name = (
        f"{random.choice(prefixes)} "
        f"{random.choice(industries)} "
        f"{random.choice(suffixes)}"
    )

    # Row creation
    rows.append({
        "supplier_id": f"SUP{i+1:06}",
        "supplier_name": name,
        "supplier_category": category,
        "country": country,
        "city": city,
        "criticality_level": criticality,
        "alternate_supplier_available": alternate,
        "onboarding_time_days": onboarding,
        "contract_value": contract_value,
        "payment_terms_days": payment
    })



# DataFrame creation

df = pd.DataFrame(rows)

print(df.head())



# Dataset info

df.info()



# Export CSV

df.to_csv(
    config["dataset"]["output_path"],
    index=False
)


