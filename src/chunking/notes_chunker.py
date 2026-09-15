"""
Semantic Section-Aware Chunker for Financial Notes to Accounts and Disclosures.
Preserves note headings, metadata, and handles token/character limits for offline RAG embedding.
"""

import re
from typing import Any, Dict, List, Optional

from src.models import NotesChunk


class NotesChunker:
    """Splits financial narrative notes into coherent, metadata-tagged chunks for RAG."""

    def __init__(self, target_chunk_size: int = 750, chunk_overlap: int = 100):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap
        self.note_split_pattern = re.compile(
            r'(?im)^[\s\t]*(?:NOTE|Note)\s+(\d+[A-Za-z]?(?:\.\d+)?)\s*[:\-\.]?\s*([^\r\n]+)'
        )

    def _split_into_sections(self, text: str) -> List[Dict[str, Any]]:
        """Splits continuous text into distinct note sections using header regex."""
        matches = list(self.note_split_pattern.finditer(text))
        if not matches:
            alt_matches = list(re.finditer(r'(?m)^[\s\t]*(\d+)[\.\)]\s+([A-Za-z][^\r\n]+)', text))
            if alt_matches:
                sections = []
                for i, m in enumerate(alt_matches):
                    start = m.start()
                    end = alt_matches[i + 1].start() if i + 1 < len(alt_matches) else len(text)
                    sections.append({
                        "note_number": m.group(1),
                        "note_title": f"Note {m.group(1)} - {m.group(2).strip()}",
                        "content": text[start:end].strip()
                    })
                return sections

            if text.strip():
                return [{
                    "note_number": None,
                    "note_title": "Notes to the Financial Statements",
                    "content": text.strip()
                }]
            return []

        sections = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            note_num = m.group(1)
            raw_title = m.group(2).strip()
            full_title = f"Note {note_num} - {raw_title}" if not raw_title.lower().startswith("note") else raw_title
            content = text[start:end].strip()
            sections.append({
                "note_number": note_num,
                "note_title": full_title,
                "content": content
            })
        return sections

    def _sliding_window_chunks(self, text: str, header_prefix: str) -> List[str]:
        """Chunks text into sliding windows, respecting paragraph/sentence boundaries."""
        if len(text) <= self.target_chunk_size:
            return [f"{header_prefix}\n\n{text}".strip()]

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [p.strip() for p in text.splitlines() if p.strip()]

        chunks = []
        current_chunk = []
        current_length = 0

        for p in paragraphs:
            p_len = len(p)
            if current_length + p_len > self.target_chunk_size and current_chunk:
                chunk_str = "\n\n".join(current_chunk)
                chunks.append(f"{header_prefix}\n\n{chunk_str}".strip())
                if len(current_chunk[-1]) <= self.chunk_overlap:
                    current_chunk = [current_chunk[-1], p]
                    current_length = len(current_chunk[0]) + p_len
                else:
                    current_chunk = [p]
                    current_length = p_len
            else:
                current_chunk.append(p)
                current_length += p_len

        if current_chunk:
            chunk_str = "\n\n".join(current_chunk)
            chunks.append(f"{header_prefix}\n\n{chunk_str}".strip())

        return chunks

    def chunk_notes(
        self,
        raw_sections: List[Dict[str, str]],
        full_text: str,
        company_name: str,
        fiscal_period: str,
        statement_id: str,
        source_file: str
    ) -> List[NotesChunk]:
        """Transforms raw extracted narrative sections into RAG-ready NotesChunks."""
        combined_sections = []
        if raw_sections:
            for sec in raw_sections:
                sec_text = sec.get("text", "")
                extracted = self._split_into_sections(sec_text)
                combined_sections.extend(extracted)
        elif full_text:
            combined_sections = self._split_into_sections(full_text)

        if not combined_sections:
            return []

        chunks: List[NotesChunk] = []

        for sec in combined_sections:
            note_num = sec["note_number"]
            note_title = sec["note_title"]
            content = sec["content"]

            header_context = f"[{company_name} | {fiscal_period} | {note_title}]"
            text_chunks = self._sliding_window_chunks(content, header_prefix=header_context)

            total_chunks = len(text_chunks)
            for idx, c_text in enumerate(text_chunks):
                cid = f"{statement_id}_note_{note_num or 'general'}_{idx+1}"
                char_len = len(c_text)
                est_tokens = max(1, char_len // 4)

                metadata = {
                    "company_name": company_name,
                    "fiscal_period": fiscal_period,
                    "statement_id": statement_id,
                    "note_number": note_num,
                    "note_title": note_title,
                    "chunk_index": idx,
                    "total_chunks_in_note": total_chunks,
                    "source_file": source_file,
                    "type": "notes_to_accounts"
                }

                chunks.append(
                    NotesChunk(
                        chunk_id=cid,
                        statement_id=statement_id,
                        company_name=company_name,
                        fiscal_period=fiscal_period,
                        note_number=note_num,
                        note_title=note_title,
                        chunk_index=idx,
                        total_chunks_in_note=total_chunks,
                        text=c_text,
                        character_count=char_len,
                        estimated_tokens=est_tokens,
                        metadata=metadata
                    )
                )

        return chunks
