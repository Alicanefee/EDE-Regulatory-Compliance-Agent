"""
Excel Writer (openpyxl + hash chain)
=====================================

Wraps openpyxl for writing audit-trail events to .xlsx with hash chain.

6 sheets (see docs/architecture.md):
- Process: timestamp, step, status, agent, duration, prev_hash, this_hash
- Documents: doc_id, name, type, upload_date, status, source_authority
- Classification: device_name, intended_use, class, rule_id, justification, version_snapshot
- Validation: doc_id, requirement, result, missing_items, notes, prev_hash, this_hash
- API_Log: timestamp, agent, model, tokens, cost, latency
- Audit: hash_chain_verification results

TODO (v0.2): Implement. See src/agents/excel_logger.py for the hash chain logic.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any


SHEETS = ["Process", "Documents", "Classification", "Validation", "API_Log", "Audit"]


class ExcelWriter:
    """openpyxl wrapper with hash-chain audit trail."""

    def __init__(self, xlsx_path: str | Path) -> None:
        self.xlsx_path = Path(xlsx_path)
        # TODO: initialize workbook if not exists
        # import openpyxl
        # if self.xlsx_path.exists():
        #     self.wb = openpyxl.load_workbook(self.xlsx_path)
        # else:
        #     self.wb = openpyxl.Workbook()
        #     self._init_sheets()

    def _init_sheets(self) -> None:
        """Initialize 6 sheets with their column headers."""
        # TODO (v0.2)
        # for sheet_name in SHEETS:
        #     ws = self.wb.create_sheet(sheet_name)
        #     ws.append(self._get_headers(sheet_name))
        pass

    def append_row(self, sheet: str, row_data: dict) -> None:
        """Append a row to a sheet."""
        # TODO (v0.2)
        pass

    def save(self) -> None:
        """Save the workbook to disk."""
        # TODO (v0.2)
        # self.wb.save(self.xlsx_path)
        pass
