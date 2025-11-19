# Data Migration Validation (100-Customer Demo)

This project demonstrates a clean and easy-to-understand **data migration validation workflow** using a sample of **100 customer records**. It shows how to ensure that data is correctly migrated from an **OLD system** to a **NEW system** by performing row count checks, primary key checks, null checks, schema validation, and mismatch detection.

The final results are displayed in a clean HTML report hosted on GitHub Pages.

### 🔗 Live Report  
View the report here:  
**https://mohanreddy6.github.io/Data-Migration-Validation/sample-report.html**

---

## 🚀 Project Purpose

When companies move from one system to another (databases, applications, CRM, billing systems), it is critical to verify that all data has been:

- correctly migrated  
- not lost  
- not duplicated  
- not changed unexpectedly  
- consistent in format and schema  

This project simulates a real migration validation workflow using simple, understandable data so that the validation logic is clear.

---

## 📊 Data Used (100 Customers)

Each customer has these fields:

| Column        | Description                         |
|---------------|-------------------------------------|
| `customer_id` | Unique ID (primary key)             |
| `name`        | Customer full name                  |
| `email`       | Email address                       |
| `dob`         | Date of birth                       |
| `balance`     | Account balance                     |
| `status`      | ACTIVE / INACTIVE status            |

Two datasets are compared:

- **OLD dataset** → data from the legacy system  
- **NEW dataset** → data after migration  

---

## ✔️ Validation Checks Performed

### 1. **Row Count Validation**
Ensures both systems have the same number of customers.  
Example: OLD = 100, NEW = 100 → PASS

### 2. **Primary Key Validation**
Checks for:
- primary key duplicates in OLD  
- primary key duplicates in NEW  
- one-to-one mapping of IDs  

Both datasets must have the same `customer_id` values.

### 3. **Null Check**
Required fields such as `name` and `email` must not have nulls.

### 4. **Schema Validation**
Ensures column names and data types match between OLD and NEW systems.

### 5. **Mismatch Detection**
Identifies specific value differences for each customer.

Example mismatches:
- Name difference  
- Email difference  
- DOB swapped  
- Balance difference  
- Status difference  

Only **5 mismatches** are intentionally included to keep the demo simple.

---

## 📄 Output Report (HTML)

The final results are shown in a clean HTML report that includes:

- Summary of totals
- Validation checklist
- Explanation of each check
- Mismatch table (5 mismatches)
- Row count table
- Null summary
- Schema comparison
- One-to-one mapping confirmation  

This HTML is fully self-contained and can be viewed locally or online.

---

## 🧭 How to View the Report Locally (VS Code)

1. Open folder in VS Code  
2. Install “Live Server” extension  
3. Right-click `sample-report.html` → **Open with Live Server**  
4. Browser opens with live preview  
5. Any edits reload instantly  

---

## 🔧 Project Structure

