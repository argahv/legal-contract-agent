"""Legal-grade chunking — preserves numbered sections while bounding context windows."""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter


def legal_chunker() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=[
            "\n\nARTICLE ",
            "\n\nSECTION ",
            "\n\n§",
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )
