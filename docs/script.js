function parseCSV(text) {
    const lines = text.trim().split("\n");
    const headers = lines[0].split(",").map(h => h.trim());

    const rows = lines.slice(1).map(line => {
        const cols = line.split(",");
        let obj = {};

        headers.forEach((h, i) => {
            obj[h] = cols[i] ? cols[i].trim() : "";
        });

        return obj;
    });

    return { headers, rows };
}

function clearResults() {
    document.getElementById("results").innerText = "No results yet.";
    document.getElementById("summary").style.display = "none";
}

function validate() {
    const oldFile = document.getElementById("oldFile").files[0];
    const newFile = document.getElementById("newFile").files[0];

    if (!oldFile || !newFile) {
        alert("Please upload both OLD and NEW CSV files.");
        return;
    }

    Promise.all([oldFile.text(), newFile.text()]).then(data => {
        const oldCSV = parseCSV(data[0]);
        const newCSV = parseCSV(data[1]);

        let output = "";
        let summary = {
            rowCountPass: false,
            schemaPass: false,
            mismatches: 0,
            missingIDs: 0,
            duplicatePKs: 0,
            nullIssues: 0,
            typeErrors: 0
        };

        // === Row Count Check ===
        output += "=== ROW COUNT CHECK ===\n";
        output += `Old Rows: ${oldCSV.rows.length}\n`;
        output += `New Rows: ${newCSV.rows.length}\n`;

        summary.rowCountPass = oldCSV.rows.length === newCSV.rows.length;
        output += summary.rowCountPass ? "PASS\n\n" : "FAIL\n\n";

        // === Schema Check ===
        output += "=== SCHEMA CHECK ===\n";
        output += `Old Columns: ${oldCSV.headers.join(", ")}\n`;
        output += `New Columns: ${newCSV.headers.join(", ")}\n`;

        summary.schemaPass = oldCSV.headers.join() === newCSV.headers.join();
        output += summary.schemaPass ? "PASS\n\n" : "FAIL\n\n";

        // Convert new to map
        const newMap = {};
        newCSV.rows.forEach(r => newMap[r.customer_id] = r);

        // === Missing IDs Check ===
        output += "=== MISSING ID CHECK ===\n";
        const oldIDs = oldCSV.rows.map(r => r.customer_id);
        const newIDs = newCSV.rows.map(r => r.customer_id);

        oldIDs.forEach(id => {
            if (!newMap[id]) {
                output += `Missing in NEW → ${id}\n`;
                summary.missingIDs++;
            }
        });

        newIDs.forEach(id => {
            if (!oldIDs.includes(id)) {
                output += `Extra in NEW → ${id}\n`;
                summary.missingIDs++;
            }
        });

        if (summary.missingIDs === 0) output += "No missing IDs.\n";
        output += "\n";

        // === Duplicate PK Check ===
        output += "=== DUPLICATE PRIMARY KEY CHECK ===\n";

        function countDuplicates(list) {
            const seen = new Set();
            const dups = new Set();
            list.forEach(id => {
                if (seen.has(id)) dups.add(id);
                seen.add(id);
            });
            return Array.from(dups);
        }

        const oldDups = countDuplicates(oldIDs);
        const newDups = countDuplicates(newIDs);

        if (oldDups.length === 0 && newDups.length === 0) {
            output += "No duplicates.\n\n";
        } else {
            oldDups.forEach(id => output += `Duplicate in OLD: ${id}\n`);
            newDups.forEach(id => output += `Duplicate in NEW: ${id}\n`);
            summary.duplicatePKs = oldDups.length + newDups.length;
            output += "\n";
        }

        // === Null Check ===
        output += "=== NULL VALUE CHECK ===\n";
        oldCSV.rows.forEach(r => {
            oldCSV.headers.forEach(h => {
                if (r[h] === "") {
                    output += `OLD Null → ID ${r.customer_id}, Field ${h}\n`;
                    summary.nullIssues++;
                }
            });
        });

        newCSV.rows.forEach(r => {
            newCSV.headers.forEach(h => {
                if (r[h] === "") {
                    output += `NEW Null → ID ${r.customer_id}, Field ${h}\n`;
                    summary.nullIssues++;
                }
            });
        });

        if (summary.nullIssues === 0) output += "No null values.\n";
        output += "\n";

        // === Data Type Validation ===
        output += "=== DATA TYPE VALIDATION ===\n";

        function validEmail(email) {
            return /\S+@\S+\.\S+/.test(email);
        }

        function validDate(date) {
            return /^\d{4}-\d{2}-\d{2}$/.test(date);
        }

        function validNumber(n) {
            return !isNaN(parseFloat(n));
        }

        newCSV.rows.forEach(r => {
            if (!validEmail(r.email)) {
                output += `Invalid Email → ${r.customer_id}: ${r.email}\n`;
                summary.typeErrors++;
            }
            if (!validDate(r.dob)) {
                output += `Invalid DOB → ${r.customer_id}: ${r.dob}\n`;
                summary.typeErrors++;
            }
            if (!validNumber(r.balance)) {
                output += `Invalid Balance → ${r.customer_id}: ${r.balance}\n`;
                summary.typeErrors++;
            }
        });

        if (summary.typeErrors === 0) output += "All data types valid.\n";

        document.getElementById("results").innerText = output;

        // === Summary Box ===
        let s = "";
        s += `Row Count Check: <span class="${summary.rowCountPass ? 'pass' : 'fail'}">${summary.rowCountPass ? 'PASS' : 'FAIL'}</span><br>`;
        s += `Schema Check: <span class="${summary.schemaPass ? 'pass' : 'fail'}">${summary.schemaPass ? 'PASS' : 'FAIL'}</span><br>`;
        s += `Missing ID Issues: ${summary.missingIDs}<br>`;
        s += `Duplicate PK Issues: ${summary.duplicatePKs}<br>`;
        s += `Null Value Issues: ${summary.nullIssues}<br>`;
        s += `Data Type Issues: ${summary.typeErrors}<br>`;

        document.getElementById("summaryContent").innerHTML = s;
        document.getElementById("summary").style.display = "block";
    });
}
