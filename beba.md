# SAMCO Project Controls Hub — Data Structure

## 📁 Folder Structure

```
projects/
├── _PROJECT_TEMPLATE/                    # Template for new projects
│   ├── project_manifest.json
│   ├── data/
│   │   ├── import_templates/           # All CSV files go here
│   │   │   ├── activities.csv
│   │   │   ├── wbs.csv
│   │   │   ├── contracts.csv
│   │   │   ├── payments.csv
│   │   │   ├── risks.csv
│   │   │   ├── s_curve.csv
│   │   │   ├── steel_status.csv
│   │   │   ├── delay_events.csv
│   │   │   ├── claim_evidence.csv
│   │   │   ├── letters.csv
│   │   │   ├── resources.csv
│   │   │   ├── equipment.csv
│   │   │   ├── daily_logs.csv
│   │   │   ├── change_orders.csv
│   │   │   ├── quality_inspections.csv
│   │   │   └── safety_incidents.csv
│   │   └── db/                          # SQLite database (auto-created)
│   ├── reports/                          # Generated reports
│   ├── exports/                          # Excel/Word exports
│   ├── slides/                           # PowerPoint exports
│   └── inbox/                            # Letters & correspondence
│
├── Oil_Gas/
│   ├── Offshore_Platform_Alpha/
│   ├── Pipeline_Corridor_B/
│   ├── Refinery_Upgrade_C/
│   └── LNG_Terminal_D/
│
├── Infrastructure/
│   ├── Highway_Extension_101/
│   ├── Metro_Line_Phase2/
│   ├── Bridge_Crossing_X/
│   └── Airport_Terminal_3/
│
├── Energy/
│   ├── Solar_Farm_500MW/
│   ├── Wind_Park_North/
│   ├── Hydroelectric_Dam_X/
│   └── Grid_Modernization_Y/
│
├── Industrial/
│   ├── Steel_Mill_Modernization/
│   ├── Chemical_Plant_B/
│   ├── Manufacturing_Hub_C/
│   └── Robotics_Assembly_D/
│
└── Commercial/
    ├── Tower_Complex_A/
    ├── Mall_Expansion_B/
    ├── Office_Park_C/
    └── Hotel_Resort_D/
```

## 📊 CSV Files Description

| # | File | Description | Records |
|---|------|-------------|---------|
| 1 | **activities.csv** | Project activities with progress, dates, costs | ~610 total |
| 2 | **wbs.csv** | Work Breakdown Structure (18 levels per project) | ~360 total |
| 3 | **contracts.csv** | Contract details, values, terms | ~74 total |
| 4 | **payments.csv** | Payment certificates, invoices, amounts | ~517 total |
| 5 | **risks.csv** | Risk register with probability, impact, scores | ~197 total |
| 6 | **s_curve.csv** | Monthly planned vs actual progress | ~480 total |
| 7 | **steel_status.csv** | Material availability tracking | ~239 total |
| 8 | **delay_events.csv** | Delay events with impact analysis | ~94 total |
| 9 | **claim_evidence.csv** | Supporting docs for claims | ~115 total |
| 10 | **letters.csv** | Correspondence register | ~415 total |
| 11 | **resources.csv** | Personnel allocation and rates | ~703 total |
| 12 | **equipment.csv** | Equipment fleet tracking | ~336 total |
| 13 | **daily_logs.csv** | Daily site reports | ~600 total |
| 14 | **change_orders.csv** | Variations and modifications | ~113 total |
| 15 | **quality_inspections.csv** | QA/QC inspection records | ~529 total |
| 16 | **safety_incidents.csv** | HSE incident reports | ~162 total |

## 🔑 Key Columns

### activities.csv
- `project_id`, `activity_id`, `activity_name`, `wbs_code`
- `planned_start`, `planned_finish`, `actual_start`, `actual_finish`
- `progress_percent`, `status`, `budget`, `actual_cost`

### contracts.csv
- `project_id`, `contract_id`, `contract_name`, `contractor_name`
- `contract_type`, `contract_value`, `currency`, `status`
- `signed_date`, `start_date`, `end_date`, `payment_terms`

### payments.csv
- `project_id`, `contract_id`, `payment_id`, `invoice_number`
- `invoice_date`, `amount_invoiced`, `amount_certified`, `amount_paid`
- `status`, `payment_date`, `retention_deducted`

### risks.csv
- `project_id`, `risk_id`, `risk_description`, `category`
- `probability`, `impact`, `risk_score`, `status`
- `mitigation_plan`, `owner`, `identified_date`

## 🚀 How to Use

1. Copy `_PROJECT_TEMPLATE/` and rename for your new project
2. Update `project_manifest.json` with project details
3. Replace CSV files with your real data (keep same column names)
4. Run: `python dashboard.py`

## 👤 Developer

**Developed & Created | Engr. Ahmed Labib**
**SAMCO Project Controls Intelligence Hub**
