function parseCSV(content) {
    const rows = content.trim().split("\n");
    const headers = rows[0].split(",");

    const data = rows.slice(1).map(row => {
        const cols = row.split(",");
        let obj = {};
        headers.forEach((h, i) => {
            obj[h.trim()] = cols[i] ? cols[i].trim() : "";
        });
        return obj;
    });

    return { headers, data };
}

function validate() {
    const oldFile = document.getElementById("oldFile").files[0];
    const newFile = document.getElementById("newFile").files[0];

    if (!oldFile || !newFile) {
        alert("Please upload both OLD and NEW CSV files.");
        return;
    }

    Promise.all([oldFile.text(), newFile.text()]).then(files => {
        const oldCSV = parseCSV(files[0]);
        const newCSV = parseCSV(files[1]);

        let output = "=== Data Migration Validation Results ===\n\n";

        // 1. Row Count Check
        output += `Old Rows: ${oldCSV.data.length}\n`;
        output += `New Rows: ${newCSV.data.length}\n`;
        if (oldCSV.data.length === newCSV.data.length) {
            output += "Row Count: PASS\n\n";
        } else {
            output += "Row Count: FAIL\n\n";
        }

        // 2. Schema Check
        output += "=== Schema Check ===\n";
        output += `Old Columns: ${oldCSV.headers.join(", ")}\n`;
        output += `New Columns: ${newCSV.headers.join(", ")}\n`;

        if (oldCSV.headers.join() === newCSV.headers.join()) {
            output += "Schema: PASS\n\n";
        } else {
            output += "Schema: FAIL\n\n";
        }

        // Convert NEW data to dictionary for fast lookup
        const newMap = {};
        newCSV.data.forEach(row => {
            newMap[row["customer_id"]] = row;
        });

        // 3. Value Comparison
        output += "=== Value Mismatches ===\n";
        let mismatchCount = 0;

        oldCSV.data.forEach(oldRow => {
            const id = oldRow["customer_id"];
            const newRow = newMap[id];

            if (!newRow) {
                output += `Missing in NEW: Customer ID ${id}\n`;
                mismatchCount++;
                return;
            }

            oldCSV.headers.forEach(h => {
                if (oldRow[h] !== newRow[h]) {
                    output += `Mismatch (ID ${id}): ${h} → OLD="${oldRow[h]}", NEW="${newRow[h]}"\n`;
                    mismatchCount++;
                }
            });
        });

        if (mismatchCount === 0) {
            output += "No mismatches found.\n";
        }

        // 4. Null Check
        output += "\n=== Null Value Check ===\n";
        let nulls = 0;

        oldCSV.data.forEach(row => {
            oldCSV.headers.forEach(h => {
                if (row[h] === "") {
                    output += `OLD Null: ID ${row["customer_id"]} Field "${h}"\n`;
                    nulls++;
                }
            });
        });

        newCSV.data.forEach(row => {
            newCSV.headers.forEach(h => {
                if (row[h] === "") {
                    output += `NEW Null: ID ${row["customer_id"]} Field "${h}"\n`;
                    nulls++;
                }
            });
        });

        if (nulls === 0) {
            output += "No null values found.\n";
        }

        document.getElementById("results").innerText = output;
    });
}
