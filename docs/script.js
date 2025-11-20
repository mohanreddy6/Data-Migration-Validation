// Parse CSV into headers + rows
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

// Clear results UI
function clearResults() {
    document.getElementById("results").innerHTML = "No results yet.";
    document.getElementById("summary").style.display = "none";
}

// Utility: duplicate finder
function findDuplicates(list) {
    const seen = new Set();
    const dups = new Set();
    list.forEach(id => {
        if (seen.has(id)) dups.add(id);
        seen.add(id);
    });
    return Array.from(dups);
}

// Validators
function validEmail(email) {
    return /\S+@\S+\.\S+/.test(email);
}

function validDate(date) {
    return /^\d{4}-\d{2}-\d{2}$/.test(date);
}

function validNumber(num) {
    return !isNaN(parseFloat(num));
}

// Build generic issue tables
function buildIssueTable(title, rows, columns) {
    let html = `<h3>${title}</h3>`;
    if (!rows || rows.length === 0) {
        html += `<p>No ${title.toLowerCase()}.</p>`;
        return html;
    }

    html += `<table style="border-collapse: collapse; width:100%; margin-top:8px; margin-bottom:20px; font-size:13px;">`;
    html += `<tr style="background:#f0f0f0; font-weight:bold;">`;

    columns.forEach(col => {
        html += `<td style="border:1px solid #ccc; padding:6px;">${col.label}</td>`;
    });
    html += `</tr>`;

    rows.forEach(r => {
        // color per type
        let bg = "";
        if (r.type === "missing" || r.type === "extra") {
            bg = "background:#fff8cc;"; // yellow
        } else if (r.type === "duplicate") {
            bg = "background:#ffe0b3;"; // orange
        } else if (r.type === "null") {
            bg = "background:#f0f0f0;"; // grey
        } else if (r.type === "format") {
            bg = "background:#d9e8ff;"; // light blue
        } else if (r.type === "mismatch") {
            bg = "background:#ffd6d6;"; // light red
        }

        html += `<tr class="result-row" data-id="${r.id || ""}" data-type="${r.type}" data-field="${r.field || ""}" style="${bg}">`;
        columns.forEach(col => {
            const val = r[col.key] !== undefined ? r[col.key] : "";
            html += `<td style="border:1px solid #ccc; padding:6px;">${val}</td>`;
        });
        html += `</tr>`;
    });

    html += `</table>`;
    return html;
}

// MAIN VALIDATION FUNCTION
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

        // Summary metrics
        let summary = {
            rowCountPass: false,
            schemaPass: false,
            missingCount: 0,
            extraCount: 0,
            duplicateCount: 0,
            nullCount: 0,
            formatCount: 0,
            mismatchCount: 0
        };

        const hasEmail = newCSV.headers.includes("email");
        const hasDob = newCSV.headers.includes("dob");
        const hasBalance = newCSV.headers.includes("balance");

        // Build ID arrays and maps
        const oldIDs = oldCSV.rows.map(r => r.customer_id);
        const newIDs = newCSV.rows.map(r => r.customer_id);

        const newMap = {};
        newCSV.rows.forEach(r => {
            newMap[r.customer_id] = r;
        });

        let html = "";

        // 1) Row Count + Schema
        summary.rowCountPass = oldCSV.rows.length === newCSV.rows.length;
        summary.schemaPass = oldCSV.headers.join() === newCSV.headers.join();

        html += `<h3>Row Count & Schema Checks</h3>`;
        html += `<p>Old Rows: ${oldCSV.rows.length}<br>New Rows: ${newCSV.rows.length}<br>`;
        html += `Row Count: <span style="font-weight:bold; color:${summary.rowCountPass ? 'green' : 'red'};">${summary.rowCountPass ? 'PASS' : 'FAIL'}</span><br>`;
        html += `Schema Match: <span style="font-weight:bold; color:${summary.schemaPass ? 'green' : 'red'};">${summary.schemaPass ? 'PASS' : 'FAIL'}</span></p>`;

        // 2) Missing / Extra IDs
        let missingRows = [];
        let extraRows = [];

        oldIDs.forEach(id => {
            if (!newMap[id]) {
                missingRows.push({
                    id: id,
                    type: "missing",
                    field: "customer_id",
                    source: "OLD",
                    details: "Present in OLD, missing in NEW"
                });
            }
        });

        newIDs.forEach(id => {
            if (!oldIDs.includes(id)) {
                extraRows.push({
                    id: id,
                    type: "extra",
                    field: "customer_id",
                    source: "NEW",
                    details: "Present in NEW, not in OLD"
                });
            }
        });

        summary.missingCount = missingRows.length;
        summary.extraCount = extraRows.length;

        html += buildIssueTable(
            "Missing IDs (Present in OLD, missing in NEW)",
            missingRows,
            [
                { key: "id", label: "Customer ID" },
                { key: "source", label: "Source" },
                { key: "details", label: "Details" }
            ]
        );

        html += buildIssueTable(
            "Extra IDs (Present in NEW, not in OLD)",
            extraRows,
            [
                { key: "id", label: "Customer ID" },
                { key: "source", label: "Source" },
                { key: "details", label: "Details" }
            ]
        );

        // 3) Duplicate Primary Keys
        let duplicateRows = [];
        const oldDups = findDuplicates(oldIDs);
        const newDups = findDuplicates(newIDs);

        oldDups.forEach(id => {
            duplicateRows.push({
                id: id,
                type: "duplicate",
                field: "customer_id",
                source: "OLD",
                details: "Duplicate ID in OLD dataset"
            });
        });

        newDups.forEach(id => {
            duplicateRows.push({
                id: id,
                type: "duplicate",
                field: "customer_id",
                source: "NEW",
                details: "Duplicate ID in NEW dataset"
            });
        });

        summary.duplicateCount = duplicateRows.length;

        html += buildIssueTable(
            "Duplicate Primary Keys",
            duplicateRows,
            [
                { key: "id", label: "Customer ID" },
                { key: "source", label: "Dataset" },
                { key: "details", label: "Details" }
            ]
        );

        // 4) Null Values
        let nullRows = [];

        oldCSV.rows.forEach(r => {
            oldCSV.headers.forEach(h => {
                if (r[h] === "") {
                    nullRows.push({
                        id: r.customer_id,
                        type: "null",
                        field: h,
                        source: "OLD",
                        value: "(empty)"
                    });
                }
            });
        });

        newCSV.rows.forEach(r => {
            newCSV.headers.forEach(h => {
                if (r[h] === "") {
                    nullRows.push({
                        id: r.customer_id,
                        type: "null",
                        field: h,
                        source: "NEW",
                        value: "(empty)"
                    });
                }
            });
        });

        summary.nullCount = nullRows.length;

        html += buildIssueTable(
            "Null / Empty Values",
            nullRows,
            [
                { key: "id", label: "Customer ID" },
                { key: "source", label: "Dataset" },
                { key: "field", label: "Field" },
                { key: "value", label: "Value" }
            ]
        );

        // 5) Data Type / Format Issues (NEW dataset)
        let formatRows = [];

        newCSV.rows.forEach(r => {
            if (hasEmail && r.email !== "" && !validEmail(r.email)) {
                formatRows.push({
                    id: r.customer_id,
                    type: "format",
                    field: "email",
                    value: r.email,
                    details: "Invalid email format"
                });
            }
            if (hasDob && r.dob !== "" && !validDate(r.dob)) {
                formatRows.push({
                    id: r.customer_id,
                    type: "format",
                    field: "dob",
                    value: r.dob,
                    details: "Invalid date format (expected YYYY-MM-DD)"
                });
            }
            if (hasBalance && r.balance !== "" && !validNumber(r.balance)) {
                formatRows.push({
                    id: r.customer_id,
                    type: "format",
                    field: "balance",
                    value: r.balance,
                    details: "Invalid numeric value"
                });
            }
        });

        summary.formatCount = formatRows.length;

        html += buildIssueTable(
            "Data Type / Format Issues (NEW dataset)",
            formatRows,
            [
                { key: "id", label: "Customer ID" },
                { key: "field", label: "Field" },
                { key: "value", label: "Value" },
                { key: "details", label: "Details" }
            ]
        );

        // 6) Value Mismatches
        let mismatchRows = [];

        oldCSV.rows.forEach(oldRow => {
            const id = oldRow.customer_id;
            const newRow = newMap[id];
            if (!newRow) return;

            oldCSV.headers.forEach(h => {
                const oldVal = oldRow[h] || "";
                const newVal = newRow[h] || "";
                if (oldVal !== newVal) {
                    mismatchRows.push({
                        id: id,
                        type: "mismatch",
                        field: h,
                        oldVal: oldVal,
                        newVal: newVal
                    });
                }
            });
        });

        summary.mismatchCount = mismatchRows.length;

        html += buildIssueTable(
            "Value Mismatches (OLD vs NEW for same ID)",
            mismatchRows,
            [
                { key: "id", label: "Customer ID" },
                { key: "field", label: "Field" },
                { key: "oldVal", label: "Old Value" },
                { key: "newVal", label: "New Value" }
            ]
        );

        // Push everything to the results box
        document.getElementById("results").innerHTML = html;

        // SUMMARY BOX DISPLAY
        let s = "";
        s += `Row Count Check: <span class="${summary.rowCountPass ? 'pass' : 'fail'}">${summary.rowCountPass ? 'PASS' : 'FAIL'}</span><br>`;
        s += `Schema Check: <span class="${summary.schemaPass ? 'pass' : 'fail'}">${summary.schemaPass ? 'PASS' : 'FAIL'}</span><br>`;
        s += `Missing IDs: ${summary.missingCount}<br>`;
        s += `Extra IDs: ${summary.extraCount}<br>`;
        s += `Duplicate PK Issues: ${summary.duplicateCount}<br>`;
        s += `Null Value Issues: ${summary.nullCount}<br>`;
        s += `Format / Type Issues: ${summary.formatCount}<br>`;
        s += `Value Mismatches: ${summary.mismatchCount}<br>`;

        document.getElementById("summaryContent").innerHTML = s;
        document.getElementById("summary").style.display = "block";
    });
}
