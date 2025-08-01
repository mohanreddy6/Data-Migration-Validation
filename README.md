# Data Migration Validation (Ready-to-Run)

A self-contained project to compare **old** vs **new** datasets during system migrations and generate a mismatch report.

## 🚀 Quick Start

```bash
# 1) (Optional) Create and activate a venv
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run the validator (uses the provided sample CSVs by default)
python src/validate.py   --old sample_data/old_customers.csv   --new sample_data/new_customers.csv   --key customer_id   --report output/mismatch_report.csv   --summary output/summary.txt   --html output/report.html
```

> The sample data is realistic and includes deliberate mismatches to demonstrate the tool.

## 🧩 What It Does
- Confirms primary key integrity (uniqueness, presence across files)
- Column-by-column comparison for type-safe mismatches
- Detects missing/new rows, changed values, and nullability drifts
- Outputs: CSV mismatch report, plain-text summary, and simple HTML report

## 🛠 Arguments
```
--old       Path to old dataset (CSV)
--new       Path to new dataset (CSV)
--key       Primary key column to join on
--report    Path to save mismatch details (CSV)
--summary   Path to save a human-readable summary
--html      Path to save a simple HTML report
--cols      (Optional) Comma-separated list of columns to compare (defaults to intersection)
```

## 📁 Project Structure
```
data-migration-validation/
├── README.md
├── requirements.txt
├── sample_data/
│   ├── old_customers.csv
│   └── new_customers.csv
├── src/
│   └── validate.py
└── output/  # generated
```

## ✅ Example Output (Summary)
```
Rows only in OLD: 5
Rows only in NEW: 3
Rows compared: 992
Changed cells (value-level): 128
Columns compared: name,email,dob,balance,status
```

## 🧪 Notes
- Uses **pandas** only; no databases or external services required.
- CSVs can be large; the script streams intelligently for summaries but loads into memory for full diff. For very large files, consider chunked comparisons.
- Extend `validate.py` to write Excel reports or integrate with CI/CD as needed.
```