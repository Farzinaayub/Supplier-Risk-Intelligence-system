| Validation Test                     | Purpose                                                          | Consequence if Failed                                                           |
| ----------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Primary Key Uniqueness              | Ensure entity records are not duplicated                         | Duplicate suppliers, POs, shipments, or incidents create inconsistent analytics |
| Mandatory Field Validation          | Ensure critical columns are populated                            | Missing operational data breaks downstream KPIs and joins                       |
| Foreign Key Validation              | Validate relational integrity across tables                      | Orphan records create unreliable supplier or shipment tracking                  |
| Quantity Validation                 | Ensure received/rejected quantities remain logically valid       | Negative or excessive quantities distort inventory and quality metrics          |
| Date Sequence Validation            | Verify chronological consistency across transactions             | Invalid timelines reduce trust in operational history                           |
| Shipment Status Validation          | Ensure quality inspections map to valid shipment states          | Inspections on invalid shipments create unrealistic operational flows           |
| Supplier-Component Mapping          | Validate supplier category aligns with component types           | Incorrect sourcing relationships reduce business realism                        |
| Inventory Sanity Checks             | Prevent negative stock, safety stock, or consumption values      | Unrealistic inventory states corrupt planning models                            |
| Usable Inventory Validation         | Ensure stock does not exceed physically usable inventory         | Inventory inflation causes misleading supply availability                       |
| Quality Correlation Validation      | Validate defect behavior against supplier performance            | Weak correlation reduces realism of quality simulations                         |
| Shipment Delay Correlation          | Ensure delayed suppliers show operational shipment impact        | Logistics incident simulations become unreliable                                |
| Audit Score Validation              | Verify audit scores remain within accepted ranges                | Invalid compliance scoring affects supplier risk analysis                       |
| Compliance Status Consistency       | Ensure compliance status aligns with audit scores                | Governance reporting becomes contradictory                                      |
| Inventory Risk Correlation          | Link low-stock conditions with supplier instability              | Risk signals lose predictive credibility                                        |
| Incident Severity Validation        | Ensure severity levels align with operational impact hours       | Incident simulation becomes statistically unrealistic                           |
| Critical Supplier Validation        | Ensure high-critical suppliers receive increased audit attention | Strategic supplier governance appears unrealistic                               |
| Statistical Distribution Validation | Validate variance and distribution realism across datasets       | Synthetic data becomes overly uniform and non-representative                    |
| Temporal Range Validation           | Restrict audits/incidents to realistic business periods          | Historical and future records become invalid                                    |
| Findings Correlation Validation     | Ensure poor audits correlate with operational findings           | Audit outputs lose enterprise realism                                           |
| Severity Distribution Validation    | Prevent unrealistic dominance of single severity classes         | Incident modeling becomes biased and unusable                                   |
| KPI Validation                      | Validate defect rates and operational KPIs                       | Executive reporting and dashboards become unreliable                            |
| Relational Realism Validation       | Ensure supplier performance patterns remain believable           | Cross-functional analytics lose trustworthiness                                 |
