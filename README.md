# Data Migration Validation Tool

This project is designed to help validate data migrations by comparing old and new datasets. It generates clear and easy-to-read reports suitable for non-technical reviewers.

## Quick Start Instructions (Windows)

Follow these steps to set up and run the validation tool:

1. **Create and activate a virtual environment:**

```batch
python -m venv .venv
.venv\Scripts\activate
```

2. **Install dependencies:**

```batch
pip install -r requirements.txt
```

3. **Run the validation script:**

```batch
python src\validate.py --old sample_data\old_customers.csv --new sample_data\new_customers.csv --key customer_id --report output\mismatch_report.csv --summary output\summary.txt --html output\report.html
```

The provided sample data contains realistic examples, including intentional mismatches for demonstration purposes.

## Purpose of the Tool

The validation tool:

* Checks primary key integrity (ensures uniqueness and presence in both datasets).
* Compares datasets column-by-column to identify mismatches.
* Identifies missing or new rows, changed values, and differences in nullability.
* Produces detailed mismatch reports (CSV format), a readable summary (text format), and a simple HTML report for easy review.

## Command Line Arguments

The script accepts the following arguments:

```
--old       Path to the old dataset CSV file.
--new       Path to the new dataset CSV file.
--key       Primary key column name used for joining datasets.
--report    File path to save detailed mismatch results in CSV format.
--summary   File path to save a plain-text summary.
--html      File path to save a simple HTML report.
--cols      Optional: Comma-separated list of columns to compare. Defaults to columns common to both datasets.
```

## Project Directory Structure

```
data-migration-validation/
├── README.md
├── requirements.txt
├── sample_data/
│   ├── old_customers.csv
│   └── new_customers.csv
├── src/
│   └── validate.py
└── output/  (generated reports will be saved here)
```

## Example Summary Output

The summary output provides a quick overview of mismatches found:

```
Rows only in OLD: 5
Rows only in NEW: 3
Rows compared: 992
Changed cells (value-level): 128
Columns compared: name,email,dob,balance,status
```

## Demonstration

* **Command Line Run:**

  A screenshot or demonstration would typically show the execution of the script in a command-line interface.

* **HTML Report:**

  A screenshot or live example typically demonstrates the HTML report generated for visual inspection.

* **Live Report Example:**

  Access a live sample report at:
  [https://mohanreddy6.github.io/data-migration-validation/sample-report.html](https://mohanreddy6.github.io/data-migration-validation/sample-report.html)

## Additional Information

* The validation tool relies solely on the pandas library, requiring no additional databases or external services.
* CSV files can be large; the tool intelligently handles summary generation but fully loads files into memory for detailed comparisons. For extremely large datasets, consider processing data in chunks.
* The script (`validate.py`) can be easily extended to generate Excel reports or integrated into automated CI/CD workflows.
