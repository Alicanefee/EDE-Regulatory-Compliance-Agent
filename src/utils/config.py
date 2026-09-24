"""
Configuration loader.

Reads from environment variables + .env file.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


# Default config
DEFAULT_CONFIG = {
    # Cohere (for rerank + LLM)
    "COHERE_API_KEY": "",
    "COHERE_CHAT_MODEL": "command-r-plus",
    "COHERE_RERANK_MODEL": "rerank-multilingual-v3.0",  # Arabic + English

    # Embeddings (FIXED — see docs/architecture.md)
    "EMBEDDING_MODEL": "BAAI/bge-m3",
    "EMBEDDING_DIM": 1024,

    # Vector store
    "VECTOR_STORE_PATH": "./data/chroma_db",
    "VECTOR_STORE_COLLECTIONS": ["ede_regulations", "user_documents", "templates", "faq"],

    # Excel
    "EXCEL_LOG_PATH": "./data/audit_log.xlsx",

    # LLM client (UnifiedLLMClient — planned, see docs/roadmap.md)
    "LLM_PROVIDER": "cohere",  # or "openai", "anthropic", "gemini", "local"
}


def load_config(env_path: str | Path = ".env") -> dict:
    """Load configuration from environment + defaults."""
    load_dotenv(env_path)
    config = DEFAULT_CONFIG.copy()
    for key in config:
        if os.getenv(key):
            config[key] = os.getenv(key)
    return config


# EDE regulatory documents to watch (docs/PLAN.md §10). Unverified — see DISCLAIMER.md.
EDE_DOCUMENTS = {
    "FDL-38-2024": {"version": "2024", "date": "2025-01-02", "name": "Federal Decree-Law No. 38 of 2024"},
    "EDE-CLASSIFICATION": {"version": "2024", "date": "—", "name": "Classification of a Product Guidelines"},
    "EDE-MDR-STANDARD": {"version": "2026", "date": "July 2026", "name": "Standard on Medical Device Reporting"},
    "DOH-RAI": {"version": "1.0", "date": "October 2025", "name": "DOH Responsible AI Standard (Abu Dhabi)"},
}
