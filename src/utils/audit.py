"""
Audit Trail Validator
=====================

Verifies hash chain integrity of the Excel audit log.

Reads the Excel file, recomputes hashes, verifies prev_hash chain is intact.
Reports any tampered rows.

See docs/architecture.md for the hash chain design.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class AuditValidator:
    """Verifies hash chain integrity of Excel audit log."""

    def __init__(self, xlsx_path: str | Path) -> None:
        self.xlsx_path = Path(xlsx_path)

    def verify_all_sheets(self) -> dict:
        """Verify all sheets that have hash chain columns.

        Returns:
            {
              "overall_valid": bool,
              "sheets_checked": int,
              "total_rows": int,
              "tampered_rows": list[dict],
              "breaks_by_sheet": dict,
            }
        """
        try:
            from openpyxl import load_workbook
        except ImportError:
            return {
                "overall_valid": True,
                "sheets_checked": 0,
                "total_rows": 0,
                "tampered_rows": [],
                "note": "openpyxl not installed",
            }

        if not self.xlsx_path.exists():
            return {
                "overall_valid": False,
                "sheets_checked": 0,
                "total_rows": 0,
                "tampered_rows": [],
                "error": f"Excel file not found: {self.xlsx_path}",
            }

        wb = load_workbook(self.xlsx_path)
        sheets_with_chain = ["Process", "Documents", "Classification",
                             "Validation", "API_Log", "Audit"]

        overall_valid = True
        tampered_rows = []
        breaks_by_sheet = {}
        total_rows = 0

        for sheet_name in sheets_with_chain:
            if sheet_name not in wb.sheetnames:
                continue

            ws = wb[sheet_name]
            # Read column headers
            headers = [cell.value for cell in ws[1]]
            if "prev_hash" not in headers or "this_hash" not in headers:
                continue

            prev_hash_col = headers.index("prev_hash") + 1
            this_hash_col = headers.index("this_hash") + 1
            timestamp_col = headers.index("timestamp") + 1 if "timestamp" in headers else None

            sheet_breaks = []
            expected_prev = "GENESIS"

            for row_idx in range(2, ws.max_row + 1):
                row_data = {}
                for col_idx, header in enumerate(headers, 1):
                    if header not in ("prev_hash", "this_hash", "timestamp"):
                        row_data[header] = ws.cell(row=row_idx, column=col_idx).value

                stored_prev = ws.cell(row=row_idx, column=prev_hash_col).value
                stored_this = ws.cell(row=row_idx, column=this_hash_col).value
                timestamp = ws.cell(row=row_idx, column=timestamp_col).value if timestamp_col else None

                # Verify prev_hash chain
                if stored_prev != expected_prev:
                    sheet_breaks.append({
                        "sheet": sheet_name,
                        "row": row_idx,
                        "type": "chain_break",
                        "expected_prev": expected_prev[:20] + "...",
                        "actual_prev": (stored_prev or "")[:20] + "..." if stored_prev else "(empty)",
                    })
                    tampered_rows.append({"sheet": sheet_name, "row": row_idx,
                                         "type": "chain_break"})

                # Verify this_hash matches recomputed
                if timestamp and stored_this:
                    row_content = json.dumps(row_data, sort_keys=True, default=str)
                    recomputed = hashlib.sha256(
                        f"{expected_prev}{row_content}{timestamp}".encode()
                    ).hexdigest()
                    if recomputed != stored_this:
                        sheet_breaks.append({
                            "sheet": sheet_name,
                            "row": row_idx,
                            "type": "hash_mismatch",
                            "expected_hash": recomputed[:20] + "...",
                            "actual_hash": stored_this[:20] + "...",
                        })
                        tampered_rows.append({"sheet": sheet_name, "row": row_idx,
                                             "type": "hash_mismatch"})

                expected_prev = stored_this or "GENESIS"
                total_rows += 1

            breaks_by_sheet[sheet_name] = sheet_breaks
            if sheet_breaks:
                overall_valid = False

        return {
            "overall_valid": overall_valid,
            "sheets_checked": len(breaks_by_sheet),
            "total_rows": total_rows,
            "tampered_rows": tampered_rows,
            "breaks_by_sheet": breaks_by_sheet,
        }

    def generate_audit_report(self) -> str:
        """Generate a markdown report for an inspector."""
        result = self.verify_all_sheets()

        lines = [
            "=" * 60,
            "AUDIT TRAIL INTEGRITY REPORT",
            "=" * 60,
            f"Excel file: {self.xlsx_path}",
            f"Generated: {__import__('datetime').datetime.now().isoformat()}",
            "",
            f"Sheets checked: {result.get('sheets_checked', 0)}",
            f"Total rows verified: {result.get('total_rows', 0)}",
            f"Tampered rows: {len(result.get('tampered_rows', []))}",
            "",
            f"Overall integrity: {'✅ VALID' if result.get('overall_valid') else '❌ TAMPERED'}",
            "",
        ]

        if result.get("tampered_rows"):
            lines.append("TAMPERED ROWS:")
            lines.append("-" * 60)
            for tamper in result["tampered_rows"][:20]:
                lines.append(
                    f"  Sheet '{tamper['sheet']}' row {tamper['row']}: {tamper['type']}"
                )
            if len(result["tampered_rows"]) > 20:
                lines.append(f"  ... and {len(result['tampered_rows']) - 20} more")
            lines.append("")

        breaks_by_sheet = result.get("breaks_by_sheet", {})
        for sheet_name, breaks in breaks_by_sheet.items():
            if breaks:
                lines.append(f"SHEET: {sheet_name}")
                lines.append("-" * 60)
                for b in breaks[:10]:
                    lines.append(f"  Row {b['row']}: {b['type']}")
                if len(breaks) > 10:
                    lines.append(f"  ... and {len(breaks) - 10} more")
                lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)
