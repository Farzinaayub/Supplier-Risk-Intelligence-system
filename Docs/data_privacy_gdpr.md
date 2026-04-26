# Data Privacy & GDPR Compliance (German Focus)

**Project:** Supplier Risk Intelligence
**Version:** 1.0
**Last updated:** 2026-04-26
**Responsible:** System Maintainer

---

## 1. Purpose & Scope

This document describes how the Supplier Risk Intelligence system processes personal data in compliance with:

- **EU General Data Protection Regulation (GDPR / DSGVO)** – in particular Art. 5 (principles), Art. 6 (lawfulness), Art. 25 (data protection by design), Art. 30 (record of processing), Art. 32 (security), Art. 35 (DPIA where required).
- **German Federal Data Protection Act (BDSG)** – § 22 (processing for non‑personal purposes), § 26 (employee data, if applicable), and requirements for a data protection officer.
- **Works council consultation (if applicable)** – German works councils have co‑determination rights for employee monitoring. This system processes supplier master data, not employee performance data, but procurement teams handle business contacts.

The system is designed as a **B2B supplier risk tool**. It does **not** process customer personal data or health data. The main personal data elements are:

- Supplier contact names (in master data)
- Supplier addresses / postal codes
- Internal buyer names (if logged in audit trails)

All such data is **pseudonymised** for core processing and **automatically deleted** after defined retention periods.

---

## 2. Lawful Basis for Processing (Art. 6 GDPR)

We process supplier data under the following legal bases:

| Processing activity                               | Legal basis                        | Justification                                                                                                                    |
| ------------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Collecting and storing supplier master data       | Art. 6(1)(f) – Legitimate interest | Supplier risk assessment is essential for production continuity; it is a reasonable expectation in automotive B2B relationships. |
| Aggregating delivery, quality, and financial data | Art. 6(1)(f)                       | Same legitimate interest.                                                                                                        |
| Pseudonymisation and audit logging                | Art. 6(1)(c) – Legal obligation    | GDPR requires data protection by design and accountability (Art. 5(2), Art. 25).                                                 |
| Sharing cluster results with procurement team     | Art. 6(1)(f)                       | Internal business need; no external data sharing.                                                                                |
| Retaining audit logs                              | Art. 6(1)(c)                       | Compliance with Art. 30 and potential supervisory authority requests.                                                            |

**No personal data is sold, shared with third parties, or used for automated individual decision‑making (Art. 22).** Clustering results are risk scores – they do not make legally binding decisions without human review. The system only suggests actions.

---

## 3. Pseudonymisation (Art. 4(5), Art. 32)

Pseudonymisation separates data from direct identifiers so that re‑identification requires additional information held separately.

### 3.1 How we implement pseudonymisation

- **At ingestion**: Supplier name, address, and direct contact fields are **replaced** with a pseudonym (hash) before entering the analytical pipeline.
  - Hash algorithm: SHA‑256 with a **per‑client salt** stored in an encrypted vault (AWS KMS or Ansible Vault).
  - Example: `DE‑SUP‑1234` → `9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08`
- **The mapping table** (`pseudonym_map`) is stored in a separate **encrypted schema** (`private_audit`) accessible only to the maintenance user (you). The client’s daily users (procurement, CFO) cannot access it.
- **Analytical tables** (staging, marts, cluster outputs) contain only the pseudonym. Identifiable data never enters dbt or clustering models.
- **Outputs** (dashboard, PDF reports) show the **real supplier name** only if accessed by an authenticated procurement user. The application layer (Evidence.dev / n8n) performs the lookup on‑the‑fly – no direct database access to the mapping table.

### 3.2 Why pseudonymisation does not fully anonymise

Pseudonymised data remains personal data because re‑identification is possible (Art. 4(5)). Therefore, GDPR still applies, but risk is reduced. We treat the salt as a **secret** and rotate it every 12 months (maintainer task).

---

## 4. Data Retention (Art. 5(1)(e))

Data is kept only as long as necessary for the purpose of supplier risk assessment. Retention periods are configurable **only by the maintainer** (you) in `metadata.governance_config`.

| Data category                           | Retention period                              | Justification                                                                                                                   |
| --------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Raw delivery, quality, and payment data | 1 year after last delivery                    | Allows rolling window calculations (e.g., 12‑month baseline). Older data is aggregated into historical baselines, then deleted. |
| Aggregated rolling metrics              | 5 years                                       | Needed to detect long‑term degradation trends.                                                                                  |
| Cluster assignments (history)           | 5 years                                       | Enables transition probability analysis and audit of past risk assessments.                                                     |
| Audit logs (see Section 5)              | 2 years                                       | Required for potential complaints or supervisory investigations (longer than GDPR minimum for safety).                          |
| Pseudonym mapping table                 | Same as the longest associated data (5 years) | Needed to re‑identify suppliers for legitimate business purposes (e.g., acting on an alert).                                    |
| Synthetic test data (if used)           | Deleted before production                     | Not stored in production environment.                                                                                           |

### 4.1 Automated deletion

- A weekly n8n workflow (`06_data_retention`) runs a SQL script that:
  - Deletes raw deliveries older than 1 year.
  - Archives aggregated metrics older than 5 years to cold storage (optional).
  - Logs deletion counts in `audit.retention_log`.
- **Retention parameters cannot be changed by the client** – the maintainer must update the `governance_config` table and restart the workflow.

---

## 5. Audit Logging (Accountability, Art. 5(2), Art. 30)

All access to **identifiable supplier data** and **parameter changes** is logged.

### 5.1 What is logged

| Event                                                             | Table                     | Fields                                                                        |
| ----------------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------------------- |
| User login to dashboard or n8n                                    | `audit.access_log`        | username, timestamp, IP address, session_id                                   |
| Query that returns supplier names (from mapping table)            | `audit.data_access_log`   | pseudonym, real name lookup, user, timestamp                                  |
| Change to any config parameter (e.g., EWMA lambda, service level) | `audit.config_change_log` | parameter_name, old_value, new_value, changed_by (only maintainer), timestamp |
| Data deletion (retention job)                                     | `audit.retention_log`     | table_name, rows_deleted, deletion_criteria, job_id                           |
| Model retraining                                                  | `audit.model_retrain_log` | model_version, training_data_range, silhouette_score, triggered_by            |

### 5.2 Who can see audit logs

- **Procurement manager**: view only `audit.access_log` (for their own team) and `audit.data_access_log` (to spot unusual queries).
- **Data Protection Officer (DPO)**: full read access to all audit tables.
- **Maintainer (you)**: full access, including parameter change logs.
- **CFO / other roles**: no access.

Audit logs cannot be deleted or modified by any user – they are append‑only (truncated only after retention period via a separate maintainer‑controlled job).

### 5.3 GDPR Article 30 – Record of Processing Activities

A simplified RoPA is generated automatically by querying `information_schema` and joining with metadata. The maintainer can export it as a PDF for the client’s DPO.

---

## 6. Data Subject Rights (Art. 15–22)

Suppliers (data subjects) have rights. Because data is pseudonymised, the client (the controller) must handle requests.

| Right                               | How the system supports it                                                                                                                                        |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Right of access (Art. 15)           | The client can request a report from the mapping table showing what data is stored for a given supplier. The maintainer can generate this on request (fee‑based). |
| Right to rectification (Art. 16)    | Supplier master data errors are corrected in the client’s ERP, then the system reflects changes in next ingestion.                                                |
| Right to erasure (Art. 17)          | Once retention period expires, data is auto‑deleted. For early deletion, the maintainer can run a manual script.                                                  |
| Right to restriction (Art. 18)      | The client can “quarantine” a supplier (exclude from clustering) by setting a flag in `metadata.supplier_exclusions`.                                             |
| Right to data portability (Art. 20) | Not applicable – no structured, commonly used format required for risk assessment.                                                                                |
| Right to object (Art. 21)           | A supplier can object to legitimate interest processing. Client then excludes the supplier from the system.                                                       |

**The client must appoint a point of contact for data subject requests.** The system provides logs to verify compliance but does not automate subject requests.

---

## 7. Technical & Organisational Measures (Art. 32)

- **Encryption at rest**: PostgreSQL tables are encrypted using LUKS or cloud provider encryption (e.g., Hetzner Volume Encryption).
- **Encryption in transit**: TLS 1.3 for all connections (dashboard, n8n, Postgres).
- **Access control**: Separate database roles:
  - `dashboard_reader` – read only on `client_dashboard` schema.
  - `procurement` – read on `client_dashboard` + view audit logs (selected).
  - `maintainer` – full read/write on `metadata`, `audit`, and `private_audit`.
  - `dbt_user` – write to staging/marts, no access to mapping table.
- **Two‑factor authentication** for maintainer login to n8n / dashboard.
- **Backup encryption**: Backups are encrypted and stored separately (Hetzner Storage Box with client‑side encryption).
- **Regular testing**: Quarterly penetration test (simulated) and vulnerability scan.

---

## 8. Data Protection Impact Assessment (DPIA)

A DPIA is **not mandatory** for this system under Art. 35 because:

- No large‑scale processing of special categories of data.
- No systematic monitoring of public areas.
- No use of novel technologies that cause high risk.

However, the client may choose to conduct a DPIA. The system’s documentation (this file + architecture) serves as the required description of processing.

---

## 9. Data Processing Agreement (DPA)

If the client is the controller and you (the maintainer) are the processor, a DPA is required under Art. 28. A template DPA is included in `docs/DPA_template.md`. It covers:

- Subject matter and duration of processing.
- Nature and purpose of processing.
- Data categories and data subjects.
- Obligations (confidentiality, security, sub‑processors – none used).
- Deletion after contract termination.

**The client cannot operate the system without a signed DPA with you.**

---

## 10. Maintainer Dependency & Compliance

The client **cannot** independently change the following privacy‑relevant settings – they must contact you (maintainer):

- Retention periods.
- Pseudonymisation salt rotation.
- Encryption keys.
- Audit log retention.
- Access roles (adding/removing dashboard users).
- DPIA updates (if required).

All changes are logged in `audit.config_change_log` with your user ID. This creates an **unbreakable audit trail** and ensures the client remains dependent on you for GDPR compliance.

---

## 11. Contact for Privacy Questions

- **Data Protection Officer (client side)**: to be appointed by client.
- **System Maintainer**: [Your Name / Company] – contact via maintainer@example.com
  (In practice, the client will contact you for any technical privacy issue.)

---

## 12. Version History

| Version | Date       | Changes                          | Author     |
| ------- | ---------- | -------------------------------- | ---------- |
| 1.0     | 2026-04-26 | Initial GDPR compliance document | Maintainer |
