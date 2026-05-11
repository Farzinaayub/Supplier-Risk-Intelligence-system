# Client Onboarding Checklist – Supplier Risk Intelligence

**System version:** 1.0.0  
**Client name:** _________________  
**Date:** _________________  
**Maintainer (you):** _________________  

This checklist ensures that the client’s data, infrastructure, and legal framework are ready for the automated supplier risk segmentation and early warning system.  
**Estimated time to complete:** 1–2 days (client efforts) plus 1 day (maintainer setup).

---

## Phase 0: Legal & Governance

- [ ] **0.1** Sign a Data Processing Agreement (DPA) – template provided in `docs/dpa_template.docx`.  
- [ ] **0.2** Confirm legal basis for processing (Art. 6 GDPR) – typically legitimate interest (Art. 6(1)(f)). Document it internally.  
- [ ] **0.3** Assign a Data Protection Officer (DPO) contact – name and email to be shared with maintainer.  
- [ ] **0.4** Agree on monthly retainer and license terms (see `maintenance_agreement_template.md`).  
- [ ] **0.5** Review the `data_privacy_gdpr.md` document and accept technical measures (pseudonymisation, audit, retention).  

---

## Phase 1: Data Source Preparation (Client’s ERP – Oracle/SAP)

### 1.1 Define which tables/views to export

- [ ] **Supplier master data** – provide a view with the following columns (rename if needed):  
  - `supplier_id` (unique, alphanumeric)  
  - `supplier_name` (optional – will be pseudonymised)  
  - `city` (string)  
  - `postal_code` (string)  
  - `country` (fixed to ‘Germany’)  
  - `latitude` & `longitude` (optional – if not provided, we derive from postal code)  
  - `lead_time_days` (integer, typical promised lead time)  

- [ ] **Delivery/order data** – provide a view with:  
  - `delivery_id` (unique)  
  - `supplier_id` (must match master)  
  - `delivery_date` (date)  
  - `promised_date` (date)  
  - `actual_receipt_date` (date, can be NULL if not yet received)  
  - `quantity_ordered` (numeric)  
  - `quantity_rejected` (numeric) – used to compute defect rate  

- [ ] **Payment data** (optional but recommended for financial risk):  
  - `supplier_id`  
  - `invoice_date`  
  - `payment_date` (actual)  
  - `invoice_amount`  

### 1.2 Decide on pseudonymisation method

- [ ] **Option A (preferred):** Client pseudonymises data at source – replace `supplier_name`, address, contact fields with a persistent pseudonym (e.g., `SUP_001`).  
  - Then the Docker adapter remains **disabled**.  
- [ ] **Option B:** Client sends raw data – maintainer enables the external Docker adapter.  
  - Client must provide a **salt** (random string) for deterministic hashing.  

- [ ] **Check:** Inform the DPO about the chosen method.  

### 1.3 Data export method

- [ ] **SFTP** – Client creates an SFTP user and folder (e.g., `/incoming/supplier_risk/`). Provide credentials to maintainer.  
- [ ] **API** – Client exposes a REST endpoint with API key. Provide URL and key.  
- [ ] **Manual CSV upload** (only for initial test) – Not for production.  

### 1.4 Data quality requirements (must be met before first run)

- [ ] `supplier_id` is not NULL and unique in master table.  
- [ ] Date fields in `YYYY-MM-DD` format.  
- [ ] `delivery_date` and `promised_date` are not both NULL for more than 5% of rows.  
- [ ] Quantity values are positive numbers or NULL (NULL treated as 0).  
- [ ] No more than 10% missing postal codes.  

If any of the above fails, the system will reject the data and alert the maintainer.

---

## Phase 2: Infrastructure Setup (Client or Maintainer)

Decide who hosts the system:

- [ ] **Option A: Client hosts** – Client provides a Linux VM (4GB RAM, 2 vCPUs, 40GB SSD) with Docker and internet access.  
- [ ] **Option B: Maintainer hosts** – Client pays a monthly hosting fee (€10–20).  

**Regardless of hosting:**  

- [ ] Open outbound port 443 (for GDELT API and webhook alerts).  
- [ ] Allow inbound access to port 5678 (n8n web UI – restrict to maintainer’s IP only).  
- [ ] Allow inbound access to port 8080 (Evidence dashboard – restrict to client’s office IP range).  

---

## Phase 3: System Deployment & Integration (Maintainer does this; client provides access)

- [ ] **3.1** Maintainer deploys latest Docker images on the target VM.  
- [ ] **3.2** Client provides SFTP/API credentials (stored in `.env` on the server).  
- [ ] **3.3** Maintainer runs initial data ingestion test (dry run) – confirms column mapping and quality.  
- [ ] **3.4** Maintainer enables the pseudonymisation adapter **if** Option B was chosen (see 1.2).  
- [ ] **3.5** Maintainer runs full pipeline (data load → dbt → clustering → Monte Carlo → alerts).  
- [ ] **3.6** Client receives first test alert via email/Slack (to confirm connectivity).  

---

## Phase 4: User Access & Dashboard

- [ ] **4.1** Client provides a list of email addresses for dashboard access (read‑only).  
- [ ] **4.2** Client selects Slack channel or email distribution list for real‑time alerts.  
- [ ] **4.3** Client designates one person as report recipient (weekly PDF).  
- [ ] **4.4** Maintainer creates Evidence dashboard users with password or SSO (optional).  

---

## Phase 5: Parameter Tuning & Review (First Month)

During the first month, maintainer will:

- [ ] Adjust EWMA lambda (default 0.2) and control limit L (default 3) to reduce false positives.  
- [ ] Set the service level target for safety stock (default 95%).  
- [ ] Calibrate financial Monte Carlo prior (beta distribution) using any historical failure data client can provide.  
- [ ] Provide a **performance report** (precision, recall of alerts) after 4 weeks.  

Client must:

- [ ] Nominate a procurement SME to review the first 5 alerts and confirm they are meaningful.  
- [ ] Report any false positives to maintainer for tuning.  

---

## Phase 6: Go‑Live & Ongoing Maintenance

- [ ] **6.1** Client signs off the pilot results.  
- [ ] **6.2** Maintainer sets the license expiry to **30 days from now** (renewed automatically upon monthly retainer payment).  
- [ ] **6.3** Schedule weekly automated runs (Monday 8 AM).  
- [ ] **6.4** Maintainer provides a **maintenance calendar**:  
  - Weekly: check pipeline logs, confirm data freshness.  
  - Monthly: retrain clustering model, review false positive rate.  
  - Quarterly: audit log review with client’s DPO.  

- [ ] **6.5** Client adds the system to their internal vendor risk management process.  

---

## Phase 7: Emergency & Support

- [ ] Client provides emergency contact (on‑call person) for outage communication.  
- [ ] Maintainer provides an SLA: response within 4 hours for data pipeline failures, 24h for tuning requests.  
- [ ] Document escalation path: `client-issue@...` → maintainer’s phone.  

---

## Sign‑off

By signing below, the client confirms that all prerequisites are met and they agree to the monthly retainer and license terms.

**Client representative:** _________________  
**Date:** _________________  

**Maintainer:** _________________  
**Date:** _________________  

---

## Appendix: Quick Reference – What the Client Must Provide (Summary)

| Item | Format | Example |
|------|--------|---------|
| Supplier master | CSV / SQL view | `supplier_id, name, city, plz, lead_time` |
| Delivery data | CSV / SQL view | `delivery_id, supplier_id, delivery_date, promised_date, actual_date, qty_ordered, qty_rejected` |
| Payment data (optional) | CSV / SQL view | `supplier_id, invoice_date, payment_date, amount` |
| SFTP or API endpoint | URL + credentials | `sftp://client‑sftp.intern` |
| Email list for alerts | Comma‑separated | `procurement@client.de, cfo@client.de` |
| Slack webhook URL (optional) | `https://hooks.slack.com/...` | Provided by client’s Slack admin |
| VM or cloud budget | Monthly cost | ~€10–30 (if client hosts) |
| DPO contact | Email address | `dpo@client.de` |