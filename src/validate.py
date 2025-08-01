#!/usr/bin/env python
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import html

def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=["", "NA", "NaN"])
    # Try to cast common types later; keep strings for join stability.
    return df

def coerce_types(old: pd.DataFrame, new: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Heuristic: if a column looks numeric in both, cast to numeric; if date-like, parse.
    common = [c for c in old.columns if c in new.columns]
    for c in common:
        o = old[c]
        n = new[c]
        def is_numeric(s: pd.Series) -> bool:
            try:
                pd.to_numeric(s.replace("", np.nan).dropna())
                return True
            except Exception:
                return False
        def is_date(s: pd.Series) -> bool:
            sample = s.replace("", np.nan).dropna().head(20)
            if sample.empty: return False
            ok = 0
            for v in sample:
                try:
                    pd.to_datetime(v, errors="raise")
                    ok += 1
                except Exception:
                    pass
            return ok >= max(3, len(sample)//2)
        if is_numeric(o) and is_numeric(n):
            old[c] = pd.to_numeric(o.replace("", np.nan), errors="coerce")
            new[c] = pd.to_numeric(n.replace("", np.nan), errors="coerce")
        elif is_date(o) and is_date(n):
            old[c] = pd.to_datetime(o.replace("", np.nan), errors="coerce")
            new[c] = pd.to_datetime(n.replace("", np.nan), errors="coerce")
    return old, new

def summarize_uniques(df: pd.DataFrame, key: str) -> dict:
    total = len(df)
    nulls = df[key].isna().sum() + (df[key] == "").sum()
    dupes = df.duplicated(subset=[key]).sum()
    return {"total": total, "null_keys": int(nulls), "duplicate_keys": int(dupes)}

def compare(old: pd.DataFrame, new: pd.DataFrame, key: str, cols: list[str] | None):
    # Set index
    old_idx = old.set_index(key, drop=False)
    new_idx = new.set_index(key, drop=False)

    old_only_keys = sorted(list(set(old_idx.index) - set(new_idx.index)))
    new_only_keys = sorted(list(set(new_idx.index) - set(old_idx.index)))
    common_keys = sorted(list(set(old_idx.index).intersection(set(new_idx.index))))

    if cols is None:
        cols = [c for c in old.columns if c in new.columns and c != key]

    # Prepare mismatch rows
    mismatches = []
    changed_cells = 0
    for k in common_keys:
        o = old_idx.loc[k, cols]
        n = new_idx.loc[k, cols]
        # If duplicates exist, turn into single rows by choosing first occurrence for comparison
        if isinstance(o, pd.DataFrame): o = o.iloc[0]
        if isinstance(n, pd.DataFrame): n = n.iloc[0]
        for c in cols:
            ov = o[c]
            nv = n[c]
            # Normalize NaN/NaT
            if pd.isna(ov) and pd.isna(nv):
                continue
            if isinstance(ov, pd.Timestamp) and isinstance(nv, pd.Timestamp):
                equal = (ov == nv)
            else:
                equal = (str(ov) == str(nv))
            if not equal:
                changed_cells += 1
                mismatches.append({
                    "key": k,
                    "column": c,
                    "old_value": None if pd.isna(ov) else str(ov),
                    "new_value": None if pd.isna(nv) else str(nv)
                })

    return old_only_keys, new_only_keys, common_keys, mismatches, cols, changed_cells

def write_csv(path: str, rows: list[dict]):
    df = pd.DataFrame(rows, columns=["key","column","old_value","new_value"])
    df.to_csv(path, index=False)

def write_summary(path: str, key: str, cols, old_stats, new_stats,
                  old_only_count, new_only_count, compared_rows, changed_cells):
    lines = []
    lines.append(f"Data Migration Validation Summary ({datetime.utcnow().isoformat()}Z)")
    lines.append("")
    lines.append(f"Primary key: {key}")
    lines.append(f"Columns compared: {','.join(cols)}")
    lines.append("")
    lines.append("[OLD]")
    lines.append(f"  Total rows: {old_stats['total']}")
    lines.append(f"  Null keys: {old_stats['null_keys']}")
    lines.append(f"  Duplicate keys: {old_stats['duplicate_keys']}")
    lines.append("[NEW]")
    lines.append(f"  Total rows: {new_stats['total']}")
    lines.append(f"  Null keys: {new_stats['null_keys']}")
    lines.append(f"  Duplicate keys: {new_stats['duplicate_keys']}")
    lines.append("")
    lines.append(f"Rows only in OLD: {old_only_count}")
    lines.append(f"Rows only in NEW: {new_only_count}")
    lines.append(f"Rows compared: {compared_rows}")
    lines.append(f"Changed cells (value-level): {changed_cells}")
    Path(path).write_text("\n".join(lines), encoding="utf-8")

def write_html(path: str, key: str, cols, old_stats, new_stats,
               old_only_keys, new_only_keys, mismatches):
    def esc(x): return html.escape(str(x)) if x is not None else ""
    rows_html = "\n".join(
        f"<tr><td>{esc(r['key'])}</td><td>{esc(r['column'])}</td><td>{esc(r['old_value'])}</td><td>{esc(r['new_value'])}</td></tr>"
        for r in mismatches[:5000]  # safety cap
    )
    html_doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Data Migration Validation Report</title>
<style>
body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; }}
code, pre {{ background: #f5f5f5; padding: 2px 4px; border-radius: 4px; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 14px; }}
th {{ background: #fafafa; text-align: left; }}
.summary {{ margin-bottom: 16px; }}
.badge {{ display: inline-block; background: #eef; padding: 2px 8px; border-radius: 12px; margin-right: 8px; }}
</style>
</head>
<body>
<h1>Data Migration Validation Report</h1>
<div class="summary">
  <span class="badge">Primary key: <b>{esc(key)}</b></span>
  <span class="badge">Columns: <b>{esc(','.join(cols))}</b></span>
  <span class="badge">OLD total: <b>{old_stats['total']}</b></span>
  <span class="badge">NEW total: <b>{new_stats['total']}</b></span>
  <span class="badge">Only in OLD: <b>{len(old_only_keys)}</b></span>
  <span class="badge">Only in NEW: <b>{len(new_only_keys)}</b></span>
  <span class="badge">Mismatches: <b>{len(mismatches)}</b></span>
</div>
<h2>Mismatched Cells (first 5000)</h2>
<table>
  <thead><tr><th>{esc(key)}</th><th>Column</th><th>Old Value</th><th>New Value</th></tr></thead>
  <tbody>
    {rows_html}
  </tbody>
</table>
</body>
</html>"""
    Path(path).write_text(html_doc, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser(description="Compare old vs new CSV datasets and report mismatches.")
    ap.add_argument("--old", required=True, help="Path to old CSV")
    ap.add_argument("--new", required=True, help="Path to new CSV")
    ap.add_argument("--key", required=True, help="Primary key column")
    ap.add_argument("--report", required=True, help="Path to write mismatch CSV")
    ap.add_argument("--summary", required=True, help="Path to write text summary")
    ap.add_argument("--html", required=True, help="Path to write HTML report")
    ap.add_argument("--cols", default=None, help="Comma-separated list of columns to compare (default=intersection)")
    args = ap.parse_args()

    old = load_csv(args.old)
    new = load_csv(args.new)

    if args.key not in old.columns or args.key not in new.columns:
        raise SystemExit(f"Primary key '{args.key}' must exist in both files. Old cols={list(old.columns)}, New cols={list(new.columns)}")

    old_stats = summarize_uniques(old, args.key)
    new_stats = summarize_uniques(new, args.key)

    old, new = coerce_types(old, new)

    cols = [c.strip() for c in args.cols.split(",")] if args.cols else None
    old_only_keys, new_only_keys, common_keys, mismatches, cols, changed_cells = compare(old, new, args.key, cols)

    # Write outputs
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.html).parent.mkdir(parents=True, exist_ok=True)

    write_csv(args.report, mismatches)
    write_summary(args.summary, args.key, cols, old_stats, new_stats,
                  len(old_only_keys), len(new_only_keys), len(common_keys), changed_cells)
    write_html(args.html, args.key, cols, old_stats, new_stats, old_only_keys, new_only_keys, mismatches)

    print(f"Done.\nReport: {args.report}\nSummary: {args.summary}\nHTML: {args.html}")

if __name__ == "__main__":
    main()
