# Data Migration Validation – Sample Project (100 Records)

This project demonstrates a complete, easy-to-understand data migration validation workflow.  
It uses two datasets (OLD and NEW) containing 100 customer records each.  
Several common validation checks are performed, and the results are combined into a simple HTML report.

### Live Report  
https://mohanreddy6.github.io/Data-Migration-Validation/sample-report.html

---

## Overview

When data is migrated from one system to another, it must be verified carefully.  
This project walks through the essential steps of data migration validation, including:

- Row count verification  
- Primary key matching  
- Null value checks  
- Schema consistency checks  
- Value-level comparison  

A few intentional mismatches exist in the NEW dataset to show how the validation detects differences.

---

## How This Project Works 

1. Load both datasets (OLD and NEW)
2. Compare the total rows
3. Check for primary key duplicates
4. Make sure required fields contain no null values
5. Confirm that both datasets share the same schema
6. Compare field-by-field values for each record
7. List mismatches
8. Generate an HTML report summarizing everything

This follows the same process used in real data migration activities in enterprise projects.

---

## Tools & Technologies Used

- **Python** – for data validation logic  
- **Pandas** – for dataset comparison  
- **HTML/CSS** – for the report  
- **GitHub Pages** – to publish the report  
- **VS Code + Live Server** – for local viewing  
- **CSV** – as the data format  

---

## My Role & Responsibilities 
Collaborated as part of a data engineering team to design and implement the end-to-end data migration validation pipeline, ensuring data integrity through automated checks and structured reporting.

**Responsibilities:**

- Designed and implemented validation checks to ensure accurate migration of customer data.  
- Performed row count validation, primary key checks, null value audits, schema comparison, and mismatch detection.  
- Created automated scripts to compare OLD and NEW system datasets.  
- Built a structured HTML summary report to present migration results clearly.  
- Worked with cross-functional teams to analyze mismatches and ensure accuracy of migrated data.  
- Maintained the project structure, documentation, and GitHub Pages deployment.  

---

## Project Structure

```text
Data-Migration-Validation/
│
├── sample-report.html
├── README.md
└── datasets/
    ├── old_customers.csv
    └── new_customers.csv
```

---

## Project Diagram

```text
          ┌────────────────────┐
          │     OLD System      │
          │   (100 Customers)   │
          └─────────┬──────────┘
                    │
                    ▼
          ┌────────────────────┐
          │  Validation Script  │
          │ - Row Count Check   │
          │ - PK Check          │
          │ - Null Check        │
          │ - Schema Check      │
          │ - Value Comparison  │
          └─────────┬──────────┘
                    │
          ┌────────────────────┐
          │     NEW System      │
          │   (100 Customers)   │
          └─────────┬──────────┘
                    │
                    ▼
        ┌─────────────────────────────┐
        │       HTML Report Builder    │
        └──────────────┬──────────────┘
                       │
                       ▼
       ┌────────────────────────────────┐
       │        GitHub Pages Host        │
       └────────────────────────────────┘
```

---

## Validation Flow 

```text
                  ┌────────────────────┐
                  │        Start        │
                  └─────────┬──────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Load OLD & NEW files │
                 └─────────┬────────────┘
                            ▼
              ┌────────────────────────────┐
              │       Row Count Check       │
              └───────┬────────────────────┘
                      │
     ┌────────────────┴──────────────┐
     ▼                               ▼
   PASS                      FAIL → Report issue
     ▼
┌─────────────────────────────┐
│     Primary Key Check       │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│        Null Check            │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│      Schema Comparison       │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│       Value Comparison       │
└──────────┬──────────────────┘
           ▼
┌─────────────────────────────┐
│    Generate HTML Report      │
└──────────┬──────────────────┘
           ▼
          End
```

---

## Architecture Diagram 

```text
                  ┌───────────────────┐
                  │  CSV Input Files  │
                  │ (OLD + NEW sets)  │
                  └─────────┬─────────┘
                            ▼
                 ┌─────────────────────┐
                 │  Data Validation    │
                 │  - Row Count        │
                 │  - PK Check         │
                 │  - Nulls            │
                 │  - Schema           │
                 │  - Comparisons      │
                 └─────────┬──────────┘
                            ▼
             ┌─────────────────────────┐
             │   HTML Report Builder    │
             └─────────┬───────────────┘
                            ▼
             ┌─────────────────────────┐
             │   GitHub Pages Output    │
             └─────────────────────────┘
```

---

## Data Pipeline Diagram 

```text
OLD CSV ───► Validation Engine ───► HTML Report ───► GitHub Pages
NEW CSV ───► Validation Engine ───► HTML Report ───► GitHub Pages
```

---

## Sample Dataset

### old_customers.csv

```text
customer_id,name,email,dob,balance,status
C001,Rahul Kumar,user1@oldmail.com,1990-01-10,1200.50,ACTIVE
C002,Meena Rao,user2@oldmail.com,1988-05-22,1800.00,INACTIVE
C003,Arjun Singh,user3@oldmail.com,1995-11-03,900.75,ACTIVE
C004,Priya N,user4@oldmail.com,1994-09-17,1400.20,ACTIVE
C005,Sameer R,user5@oldmail.com,1992-02-12,2000.00,ACTIVE
...
C100,Savitha D,user100@oldmail.com,1991-03-01,1550.00,ACTIVE
```

### new_customers.csv

```text
customer_id,name,email,dob,balance,status
C001,Rahul K,user1@newmail.com,1990-01-10,1200.50,ACTIVE
C002,Meena Rao,user2@newmail.com,1988-05-22,1800.00,INACTIVE
C003,Arjun Singh,user3@newmail.com,1995-11-03,900.75,ACTIVE
C004,Priya N,user4@newmail.com,1994-09-17,1450.20,ACTIVE
C005,Sameer R,user5@newmail.com,1992-02-12,2000.00,ACTIVE
...
C075,Kiran P,user75@newmail.com,1990-07-11,1500.00,INACTIVE
...
C100,Savitha D,user100@newmail.com,1991-03-01,1550.00,ACTIVE
```

---
## Summary

This project provides a simple but complete example of how real-world data migration validation is carried out.  
It demonstrates essential validation steps, produces a readable HTML report, and is structured in a clear way for learning and portfolio use.

