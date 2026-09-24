"""
Agent: Ingest
=============

Role: Document ingestion + standardization.

Pipeline:
1. Detect file type (PDF, DOCX, image, plain text, JSON)
2. Extract text:
   - PDF: pypdf (or pdfplumber for complex layouts)
   - DOCX: python-docx
   - Image: Tesseract OCR (with Arabic language pack)
   - JSON: parse directly
3. Detect language (en, ar, mixed) — character-range heuristic
4. Chunk by heading + clause number (max 512 tokens, overlap 50)
5. Extract metadata: source_file, doc_id, section, version_date, language
6. Output: list[chunk_dict]

Dependencies: pypdf, python-docx, pytesseract, Pillow
Arabic OCR: Tesseract Arabic language pack (tesseract-ocr-ara)
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from src.state_machine import StateContext


# Language detection — character range heuristic
ARABIC_RANGE = (0x0600, 0x06FF)
LATIN_RANGE = (0x0041, 0x024F)


def detect_language(text: str) -> str:
    """Detect language: 'en', 'ar', 'mixed', or 'unknown'.

    Heuristic: count Arabic chars vs Latin chars.
    """
    arabic_count = sum(1 for c in text if ARABIC_RANGE[0] <= ord(c) <= ARABIC_RANGE[1])
    latin_count = sum(1 for c in text if LATIN_RANGE[0] <= ord(c) <= LATIN_RANGE[1])
    total_alpha = arabic_count + latin_count
    if total_alpha == 0:
        return "unknown"
    arabic_ratio = arabic_count / total_alpha
    if arabic_ratio > 0.7:
        return "ar"
    if arabic_ratio > 0.1:
        return "mixed"
    return "en"


def extract_text_from_pdf(path: Path) -> str:
    """Extract text from PDF using pypdf (with fallback to pdfplumber)."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except ImportError:
        # Fallback: try pdfplumber
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(str(path)) as pdf:
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
            return "\n\n".join(text_parts)
        except ImportError:
            raise RuntimeError(
                "Neither pypdf nor pdfplumber is installed. "
                "Install: pip install pypdf pdfplumber"
            )


def extract_text_from_docx(path: Path) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        import docx
        doc = docx.Document(str(path))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        raise RuntimeError(
            "python-docx not installed. Install: pip install python-docx"
        )


def extract_text_from_image(path: Path) -> str:
    """OCR an image using Tesseract (with Arabic support)."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(str(path))
        # Try Arabic + English
        try:
            text_ar = pytesseract.image_to_string(img, lang="ara+eng")
        except Exception:
            text_ar = ""
        text_en = pytesseract.image_to_string(img, lang="eng")
        return text_ar + "\n\n" + text_en if text_ar else text_en
    except ImportError:
        raise RuntimeError(
            "pytesseract or Pillow not installed. Install: pip install pytesseract Pillow\n"
            "Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract\n"
            "And Arabic language pack: tesseract-ocr-ara (Debian/Ubuntu)"
        )


def extract_text_from_json(path: Path) -> str:
    """Extract text from JSON submission manifest."""
    import json
    data = json.loads(path.read_text(encoding="utf-8"))
    # Flatten to readable text
    parts = [
        f"Device: {data.get('device_name', '')}",
        f"Jurisdiction: {data.get('jurisdiction', '')}",
        f"Applicant: {data.get('applicant', '')}",
        f"Submission date: {data.get('submission_date', '')}",
        f"Target emirates: {', '.join(data.get('target_emirates', []))}",
        "",
        "Submitted documents:",
    ]
    for doc in data.get("submitted_documents", []):
        parts.append(f"  - {doc.get('name', '')} (type: {doc.get('type', '')})")
    return "\n".join(parts)


def extract_text_from_txt(path: Path) -> str:
    """Extract text from plain text file."""
    return path.read_text(encoding="utf-8", errors="replace")


def chunk_text_by_structure(text: str, max_tokens: int = 512, overlap: int = 50) -> list[str]:
    """Chunk text by heading + clause number boundaries.

    For regulatory documents, chunks should respect clause boundaries
    (e.g. "Section 5.1", "[MDS-G008-R1]", etc.) rather than just token count.
    """
    # Split on common clause boundary patterns
    # Pattern 1: blank line separator (---)
    # Pattern 2: heading lines like "Section X" or "[ID]"
    # Pattern 3: numbered clauses "1.1", "5.2.3"

    # First: split on --- separators (used in our corpus files)
    if "\n\n---\n\n" in text:
        blocks = text.split("\n\n---\n\n")
    else:
        # Fallback: split on double newlines
        blocks = re.split(r"\n\n+", text)

    chunks = []
    current_chunk = ""
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Rough token estimate: 1 token ≈ 4 chars
        block_tokens = len(block) // 4

        if block_tokens > max_tokens:
            # Block too big — split by sentences/lines
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            lines = block.split("\n")
            for line in lines:
                line_tokens = len(line) // 4
                if len(current_chunk) + line_tokens > max_tokens:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = line
                else:
                    current_chunk = (current_chunk + "\n" + line).strip() if current_chunk else line
        else:
            # Block fits — add to current chunk if space
            if len(current_chunk) + block_tokens > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = block
            else:
                current_chunk = (current_chunk + "\n\n" + block).strip() if current_chunk else block

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def extract_metadata(text: str, source_file: str) -> dict:
    """Extract metadata from a chunk (clause_id, section, etc.)."""
    metadata = {
        "source_file": source_file,
        "doc_id": hashlib.md5(source_file.encode()).hexdigest()[:12],
    }

    # Look for clause ID at the start (e.g. "[EDE-MD-R13]")
    clause_match = re.match(r"^\[([A-Z]+-[A-Z0-9-]+)\]", text)
    if clause_match:
        metadata["clause_id"] = clause_match.group(1)

    # Look for section numbers (e.g. "5.1", "Article 2.3")
    section_match = re.search(r"(?:Section|Article)\s+(\d+\.\d+)", text, re.IGNORECASE)
    if section_match:
        metadata["section"] = section_match.group(1)

    # Look for version dates (e.g. "v5.0, 22/06/2020")
    version_match = re.search(r"v(\d+\.\d+).*?(\d{2}/\d{2}/\d{4})", text)
    if version_match:
        metadata["version"] = version_match.group(1)
        metadata["version_date"] = version_match.group(2)

    metadata["language"] = detect_language(text)
    return metadata


class IngestAgent:
    """Ingests uploaded documents and outputs standardized chunks.

    Output schema (per chunk):
        {
          "chunk_id": str,           # sha256 hash of text[:50]
          "doc_id": str,             # hash of source filename
          "source_file": str,
          "section": str | None,
          "clause_id": str | None,
          "language": "en" | "ar" | "mixed",
          "page": int,
          "text": str,
          "version": str | None,
          "version_date": str | None,
          "tokens": int (approx),
        }
    """

    def ingest(self, file_path: str | Path, doc_type: str = "auto") -> list[dict]:
        """Ingest a single file and return standardized chunks."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf" or doc_type == "pdf":
            text = extract_text_from_pdf(path)
        elif suffix == ".docx" or doc_type == "docx":
            text = extract_text_from_docx(path)
        elif suffix in (".png", ".jpg", ".jpeg", ".tiff") or doc_type == "image":
            text = extract_text_from_image(path)
        elif suffix == ".json" or doc_type == "json":
            text = extract_text_from_json(path)
        elif suffix == ".txt" or doc_type == "txt":
            text = extract_text_from_txt(path)
        else:
            # Try as text file
            text = extract_text_from_txt(path)

        # Chunk
        chunks = chunk_text_by_structure(text)

        # Build chunk dicts with metadata
        result = []
        for i, chunk_text in enumerate(chunks):
            metadata = extract_metadata(chunk_text, path.name)
            chunk_id = hashlib.sha256(chunk_text.encode()).hexdigest()[:16]
            result.append({
                "chunk_id": chunk_id,
                "doc_id": metadata["doc_id"],
                "source_file": path.name,
                "section": metadata.get("section"),
                "clause_id": metadata.get("clause_id"),
                "language": metadata["language"],
                "page": i + 1,  # placeholder — would need real page tracking
                "text": chunk_text,
                "version": metadata.get("version"),
                "version_date": metadata.get("version_date"),
                "tokens": len(chunk_text) // 4,
            })
        return result


def ingest_agent(ctx: StateContext) -> dict:
    """State machine calls this for INGEST state."""
    ingest = IngestAgent()
    submission = ctx.submission_data

    chunks = []
    for doc in submission.get("submitted_documents", []):
        doc_path = doc.get("path", "")
        if not doc_path:
            continue
        try:
            doc_chunks = ingest.ingest(doc_path)
            chunks.extend(doc_chunks)
        except Exception as e:
            ctx.audit_log.append({
                "event": "ingest_error",
                "doc": doc.get("name"),
                "error": str(e),
            })

    ctx.ingested_chunks = chunks
    return {"ingested_chunks": len(chunks)}
