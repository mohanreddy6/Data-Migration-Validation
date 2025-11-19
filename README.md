# Data Migration Validation (100-Customer Demo)

This project demonstrates a simple and easy-to-understand **data migration validation workflow** using a sample of **100 customer records**. It compares the OLD system data with the NEW system data using quality checks such as row count matching, primary key validation, null checks, schema comparison, and mismatch detection. The final results are shown in a clean HTML report hosted on GitHub Pages.

### 🔗 Live Report  
https://mohanreddy6.github.io/Data-Migration-Validation/sample-report.html

---

## 📌 Project Overview

During data migration, it is important to ensure that data has been moved correctly without loss, duplication, or unexpected changes.  
This project simulates that validation process using only **100 customers** to keep it simple and easy to explain.

---

## 📊 Data Structure (100 Customers)

Each record contains the following fields:

| Column        | Description                     |
|---------------|---------------------------------|
| customer_id   | Unique primary key              |
| name          | Full customer name              |
| email         | Email address                   |
| dob           | Date of birth                   |
| balance       | Account balance                 |
| status        | ACTIVE / INACTIVE               |

Two datasets are compared:

- **OLD dataset**
- **NEW dataset**

---

## ✔️ Validation Checks

### 1. Row Count Check  
Ensures OLD and NEW have the same number of records.  
Example: OLD=100, NEW=100 → PASS

### 2. Primary Key Check  
Ensures:
- No duplicates in OLD  
- No duplicates in NEW  
- Same set of `customer_id` in both datasets

### 3. Null Check  
Required fields (`name`, `email`) must not be null.

### 4. Schema Comparison  
Checks column names and data types are identical in OLD and NEW.

### 5. Mismatch Detection  
Compares each field value in OLD vs NEW.  
This demo includes **5 mismatched rows** for explanation.

Example mismatches:
- Name change  
- Email domain updated  
- DOB swapped  
- Balance changed  
- Status changed  

---

## 📄 Output Report (HTML)

The final results are displayed in:


The report includes:

- Summary section  
- Pills showing totals  
- Validation table  
- Mismatch table  
- Row count details  
- Null summary  
- Schema comparison  
- Explanation for each item  

The HTML is fully self-contained and readable on any browser.

---

## 🔧 How to View the Report on Your Computer (VS Code)

1. Open folder in VS Code  
2. Install the **Live Server** extension  
3. Right-click `sample-report.html` → **Open with Live Server**  
4. Browser will open with the full report  
5. Any changes you make will auto-refresh

---

## 📘 Project Structure


---

## 📈 Flowchart (Data Migration Validation)

```mermaid
flowchart TD

    A[Start] --> B[Load OLD Dataset (100 Records)]
    B --> C[Load NEW Dataset (100 Records)]

    C --> D[Row Count Check]
    D -->|Pass| E[Primary Key Check]
    D -->|Fail| Z[Fail: Row Count Mismatch]

    E -->|Pass| F[Null Check]
    E -->|Fail| Z[Fail: Key Issues]

    F -->|Pass| G[Schema Comparison]
    F -->|Fail| Z[Fail: Null Issues]

    G -->|Pass| H[Mismatch Detection (5 Differences)]
    G -->|Fail| Z[Fail: Schema Misalignment]

    H --> I[Generate HTML Report]
    I --> J[Publish via GitHub Pages]

    J --> K[End - Report Ready]
