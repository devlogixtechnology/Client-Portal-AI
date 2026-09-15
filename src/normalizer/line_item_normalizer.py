"""
Line-Item Normalizer for Balance Sheet and Income Statement line items.
Normalizes heterogeneous accounting terms into canonical taxonomy keys.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from config.taxonomy import TAXONOMY_MAPPING, StatementCategory
from src.extractors.base import BaseExtractor
from src.models import NormalizedLineItem, StatementType


class LineItemNormalizer:
    """Normalizes financial table line items into standardized accounting concepts."""

    def __init__(self, custom_taxonomy: Optional[Dict[str, Dict[str, Any]]] = None):
        self.taxonomy = custom_taxonomy or TAXONOMY_MAPPING
        # Precompile lookup dict: normalized_alias -> (canonical_key, category, canonical_label)
        self.alias_lookup: Dict[str, Tuple[str, StatementType, str]] = {}
        self._build_index()

    def _clean_text(self, text: str) -> str:
        """Cleans raw line-item label for robust alias matching."""
        # Remove note references e.g. (Note 1), [Note 2], Note 3, (1), etc.
        text = re.sub(r"\(?\[?\b(?:note|see note)\s*\d+\b\]?\)?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^\d+[\.\)]\s*", "", text)  # leading item numbering e.g. 1. or 1)
        # Remove special characters except alphanumeric and basic spaces
        text = re.sub(r"[^a-zA-Z0-9\s\/\&\-]", " ", text)
        # Collapse multiple spaces
        return " ".join(text.lower().split())

    def _build_index(self):
        """Prepares fast hash lookup for all taxonomy aliases."""
        for key, data in self.taxonomy.items():
            cat = StatementType.INCOME_STATEMENT if data["category"] == StatementCategory.INCOME_STATEMENT else StatementType.BALANCE_SHEET
            label = data["canonical_label"]
            for alias in data["aliases"]:
                cleaned = self._clean_text(alias)
                self.alias_lookup[cleaned] = (key, cat, label)

    def match_item(self, label: str) -> Tuple[str, StatementType, str, float]:
        """
        Matches a raw line-item label against taxonomy.
        Returns: (standard_key, statement_type, canonical_label, confidence_score)
        """
        cleaned = self._clean_text(label)
        if not cleaned:
            return "empty_label", StatementType.UNKNOWN, label, 0.0

        # 1. Exact match in alias lookup
        if cleaned in self.alias_lookup:
            key, st_type, can_label = self.alias_lookup[cleaned]
            return key, st_type, can_label, 1.0

        # 2. Substring / Token subset matching
        cleaned_words = set(cleaned.split())
        best_match = None
        best_score = 0.0

        for alias, (key, st_type, can_label) in self.alias_lookup.items():
            alias_words = set(alias.split())
            if not alias_words:
                continue

            # Jaccard overlap on words
            intersection = cleaned_words.intersection(alias_words)
            if intersection:
                score = len(intersection) / max(len(cleaned_words), len(alias_words))
                # Boost if alias is fully contained in cleaned
                if alias in cleaned:
                    score = max(score, 0.85)
                elif cleaned in alias:
                    score = max(score, 0.80)

                if score > best_score:
                    best_score = score
                    best_match = (key, st_type, can_label)

        if best_match and best_score >= 0.70:
            key, st_type, can_label = best_match
            return key, st_type, can_label, round(best_score, 2)

        # 3. Unclassified fallback - slugify label
        slug = re.sub(r"[^a-z0-9_]", "_", cleaned.replace(" ", "_"))
        slug = re.sub(r"_+", "_", slug).strip("_")[:40] or "unclassified"
        return f"unclassified_{slug}", StatementType.UNKNOWN, label, 0.40

    def parse_table(
        self,
        table_rows: List[List[str]],
        default_currency: str = "USD",
        default_period: str = "FY",
        unit_multiplier: int = 1,
        source_prefix: str = "Table"
    ) -> List[NormalizedLineItem]:
        """
        Parses an extracted 2D table into a list of NormalizedLineItems.
        Discovers period column headers and associates values.
        """
        if not table_rows or len(table_rows) < 2:
            return []

        # Find header row with periods (e.g. 2024, 2023, Dec 31, etc.)
        header_row_idx = 0
        periods_by_col: Dict[int, str] = {}

        for idx, row in enumerate(table_rows[:4]):
            for c_idx, cell in enumerate(row):
                yr_match = re.search(r"\b(20\d{2})\b", str(cell))
                if yr_match:
                    periods_by_col[c_idx] = yr_match.group(1)
            if periods_by_col:
                header_row_idx = idx
                break

        # If no year columns found, default to column 1 as the primary amount
        if not periods_by_col:
            # Assume first numeric column is default_period
            periods_by_col[1] = default_period

        normalized_items: List[NormalizedLineItem] = []

        # Process each row after header
        for r_idx in range(header_row_idx + 1, len(table_rows)):
            row = table_rows[r_idx]
            if not row or not any(row):
                continue

            # First non-empty cell is usually the label
            label = ""
            label_col = 0
            for c_idx, cell in enumerate(row):
                val_float, _ = BaseExtractor.clean_numeric_str(cell)
                # If cell is not purely numeric and has letters, it's the label
                if cell and re.search(r"[a-zA-Z]", str(cell)) and val_float is None:
                    label = str(cell).strip()
                    label_col = c_idx
                    break

            if not label:
                # If label couldn't be detected with letters, take row[0]
                label = str(row[0]).strip() if len(row) > 0 else ""

            if not label or len(label) < 2:
                continue

            # Skip pure section divider titles with no numbers in entire row
            has_numbers = any(BaseExtractor.clean_numeric_str(c)[0] is not None for c in row[label_col+1:])
            if not has_numbers:
                continue

            # Match label to taxonomy
            std_key, st_type, can_label, conf = self.match_item(label)

            is_total = bool(re.search(r"\b(total|net income|gross profit|operating income|ebit|net profit)\b", label, re.IGNORECASE))

            # Extract amount for each known period column
            for col_idx, period_str in periods_by_col.items():
                if col_idx < len(row):
                    amt_float, raw_s = BaseExtractor.clean_numeric_str(row[col_idx])
                    if amt_float is not None:
                        normalized_items.append(
                            NormalizedLineItem(
                                standard_key=std_key,
                                canonical_label=can_label,
                                original_label=label,
                                statement_type=st_type,
                                amount=amt_float,
                                period=period_str,
                                currency=default_currency,
                                unit_multiplier=unit_multiplier,
                                raw_amount_str=raw_s,
                                confidence_score=conf,
                                is_total=is_total,
                                source_location=f"{source_prefix}:Row{r_idx+1}"
                            )
                        )

        return normalized_items
