"""Tests for LineItemNormalizer and accounting taxonomy alias resolution."""
import pytest
from src.normalizer.line_item_normalizer import LineItemNormalizer
from src.models import StatementType
from src.extractors.base import BaseExtractor

def test_numeric_cleaning():
    val, raw = BaseExtractor.clean_numeric_str("$12,450.50")
    assert val == 12450.50

    val, raw = BaseExtractor.clean_numeric_str("(3,200)")
    assert val == -3200.0

    val, raw = BaseExtractor.clean_numeric_str("-")
    assert val == 0.0

    val, raw = BaseExtractor.clean_numeric_str(None)
    assert val is None

def test_normalization_exact_and_fuzzy():
    norm = LineItemNormalizer()

    # Revenue aliases
    k, st, _, conf = norm.match_item("Total Revenue")
    assert k == "revenue"
    assert st == StatementType.INCOME_STATEMENT
    assert conf == 1.0

    k, st, _, _ = norm.match_item("Turnover")
    assert k == "revenue"

    k, st, _, _ = norm.match_item("Net Sales")
    assert k == "revenue"

    # COGS aliases
    k, st, _, _ = norm.match_item("Cost of goods sold")
    assert k == "cost_of_revenue"

    k, st, _, _ = norm.match_item("Cost of products sold")
    assert k == "cost_of_revenue"

    # Assets & Liabilities
    k, st, _, _ = norm.match_item("Cash and cash equivalents")
    assert k == "cash_and_cash_equivalents"
    assert st == StatementType.BALANCE_SHEET

    k, st, _, _ = norm.match_item("Called up share capital")
    assert k == "common_stock"

    k, st, _, _ = norm.match_item("Trade and other payables")
    assert k == "accounts_payable"

def test_table_parsing():
    norm = LineItemNormalizer()
    table = [
        ["Line Item", "2024", "2023"],
        ["Revenues", "100,000", "80,000"],
        ["Cost of sales", "40,000", "30,000"],
        ["Gross Profit", "60,000", "50,000"],
        ["Net Income", "15,000", "10,000"]
    ]
    items = norm.parse_table(table, default_currency="USD", default_period="FY2024", unit_multiplier=1)
    # Each row produces 2 items (2024 and 2023)
    assert len(items) == 8
    keys = [item.standard_key for item in items]
    assert "revenue" in keys
    assert "cost_of_revenue" in keys
    assert "gross_profit" in keys
    assert "net_income" in keys
