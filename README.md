[![CI](https://github.com/mohanreddy6/Data-Migration-Validation/actions/workflows/main.yml/badge.svg)](https://github.com/mohanreddy6/Data-Migration-Validation/actions/workflows/main.yml)
![Python](https://img.shields.io/badge/python-3.10%20|%203.11-blue)
![License](https://img.shields.io/badge/license-MIT-informational) 

# Data Migration Validation – Sample Project (100 Records)

This project presents a complete, end-to-end data migration validation workflow using two sample datasets containing 100 customer records each. It demonstrates how real migration teams validate data when moving from one system to another, using a repeatable process that checks data consistency, accuracy, completeness, and schema alignment.

check your dataset validation here:-
https://mohanreddy6.github.io/Data-Migration-Validation/sample-report.html](https://mohanreddy6.github.io/Data-Migration-Validation/)


# 1. Why This Project Exists 

A common problem in many organizations occurs during system upgrades, CRM transitions, or application modernizations: **data must be migrated from an old system into a new one**.  

It sounds simple, but in reality, the process is full of challenges. After migration, teams discover issues such as:

- Missing customer records  
- Changed primary keys  
- Incorrect balances  
- Updated email formats  
- Schema mismatches  
- Data type inconsistencies  

This leads to hours of manual checking, row-by-row comparisons, cross-verification with Excel sheets, and repeated communication between engineering, QA, and business teams.

To address this, this project was created as a **lightweight but complete validation engine** that demonstrates how professional teams verify data migration correctness.

It is designed to simulate a real-world scenario where:

- An old system exports **old_customers.csv**  
- A new system produces **new_customers.csv**  
- The validation engine compares them  
- A clear and readable HTML report is produced  

This is the exact workflow followed in enterprise migration projects.


# 2. Where This Project Can Be Used

This project is applicable to:

- Data migration POCs  
- ETL validation  
- System upgrade testing  
- CRM migration exercises  
- QA teams validating test migrations  
- Data engineering interviews or portfolio demonstrations  
- Teaching beginners how migration checks are structured  

Any process involving **source → migration → target** can use the same approach.


# 3. Overview of the Validation Approach

The validation engine performs the following checks:

1. Load both datasets (OLD and NEW)
2. Compare row counts
3. Validate primary key uniqueness and consistency
4. Check required fields for null values
5. Confirm that both datasets share the same columns
6. Perform value-level comparison (old vs new)
7. Identify mismatches
8. Produce a final HTML summary report

A few intentional mismatches are included in the NEW dataset so the report highlights differences clearly.


# 4. Tools and Technologies

- Python  
- Pandas  
- HTML/CSS for reporting  
- GitHub Pages for hosting  
- VS Code for development  
- CSV for data storage  


# 5. My Role and Responsibilities

As part of a data engineering and QA collaboration effort, my responsibilities included:

- Designing and planning the data validation workflow  
- Implementing row count, primary key, null, schema, and value-based validation checks  
- Writing the automated Python logic for comparing OLD and NEW system data  
- Developing the HTML summary report  
- Investigating mismatches and confirming expected differences  
- Maintaining documentation, dataset structure, and GitHub Pages deployment  

This reflects typical responsibilities in real data migration projects.


# 6. Project Structure

```
Data-Migration-Validation/
│
├── sample-report.html
├── README.md
└── datasets/
    ├── old_customers.csv
    └── new_customers.csv
```


# 7. Architecture Diagram

```
                  ┌───────────────────┐
                  │  CSV Input Files  │
                  │ (OLD + NEW sets)  │
                  └─────────┬─────────┘
                            ▼
                 ┌─────────────────────┐
                 │  Validation Engine   │
                 │  - Row Count         │
                 │  - PK Check          │
                 │  - Nulls             │
                 │  - Schema            │
                 │  - Value Compare     │
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


# 8. Data Pipeline Diagram

```
OLD CSV ───► Validation Engine ───► HTML Report ───► GitHub Pages
NEW CSV ───► Validation Engine ───► HTML Report ───► GitHub Pages
```


# 9. Validation Flow Diagram

```
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
   PASS                      FAIL → Record issue
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


# 10. Algorithm Diagrams

Below are the algorithms represented using ASCII flowchart shapes.

## 10.1 Overall Algorithm (Oval, Diamond, Rectangle)

```
       ┌───────────────────┐
       │      Start        │  
       └─────────┬─────────┘
                 ▼
       ┌───────────────────┐
       │ Read OLD + NEW    │ 
       │ CSV files         │
       └─────────┬─────────┘
                 ▼
     ┌────────────────────────┐
     │ Row count same?        │ 
     └─────────┬──────────────┘
               │Yes
               │
               │         No
               ▼          \
  ┌────────────────────┐    \
  │ Check primary keys │     \
  └─────────┬──────────┘      \
            ▼                  \
  ┌────────────────────┐        \
  │ Null value check   │         \
  └─────────┬──────────┘          \
            ▼                       \
  ┌────────────────────┐             \
  │ Schema comparison  │              \
  └─────────┬──────────┘               \
            ▼                            \
  ┌────────────────────┐                  \
  │ Value comparison   │                   \
  └─────────┬──────────┘                    \
            ▼                                 \
  ┌────────────────────┐                       \
  │ Build HTML report  │             \
  └─────────┬──────────┘                        \
            ▼                                     ▼
       ┌───────────────────┐            ┌───────────────────┐
       │        End        │            │ Report Issue(s)   │
       └───────────────────┘            └───────────────────┘
```


## 10.2 Value-Level Comparison Algorithm

```
        ┌───────────────────────┐
        │ For each customer_id  │
        └─────────┬─────────────┘
                  ▼
       ┌──────────────────────────┐
       │ Compare OLD vs NEW row   │
       └─────────┬───────────────┘
                 ▼
     ┌────────────────────────┐
     │ Any field different?   │
     └─────────┬──────────────┘
               │Yes
               │
               ▼
   ┌─────────────────────────────┐
   │ Add mismatch to report list │
   └─────────┬───────────────────┘
             ▼
        Continue loop
```


# 11. Sample Dataset

### old_customers.csv (Excerpt)

```
customer_id,name,email,dob,balance,status
C001,Rahul Kumar,user1@oldmail.com,1990-01-10,1200.50,ACTIVE
C002,Meena Rao,user2@oldmail.com,1988-05-22,1800.00,INACTIVE
...
```

### new_customers.csv (Excerpt)

```
customer_id,name,email,dob,balance,status
C001,Rahul K,user1@newmail.com,1990-01-10,1200.50,ACTIVE
C002,Meena Rao,user2@newmail.com,1988-05-22,1800.00,INACTIVE
...
```


# 12. Summary

This project demonstrates how real-world data migration validation is planned, executed, and documented.  
It includes complete checks, mismatch detection, automated reporting, and a clear structure suitable for learning, interviews, or practical use.

It provides a realistic blueprint for enterprise migration testing and can be adapted easily for larger datasets or production systems.

