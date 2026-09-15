"""
Standard Financial Statement Taxonomy for Line-Item Normalization.
Maps varied accounting standards (US GAAP, IFRS, UK FRS 102, SME custom terminology)
to canonical keys with statement category tagging.
"""

from enum import Enum
from typing import Dict, List, Optional

class StatementCategory(str, Enum):
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"

TAXONOMY_MAPPING: Dict[str, Dict[str, any]] = {
    # ------------------ INCOME STATEMENT ------------------
    "revenue": {
        "canonical_label": "Total Revenue",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "revenue", "revenues", "total revenue", "total revenues", "net revenue",
            "net revenues", "net sales", "sales revenue", "gross revenue",
            "turnover", "net turnover", "operating revenue", "sales", "gross sales",
            "billings", "total billings", "client billings"
        ]
    },
    "cost_of_revenue": {
        "canonical_label": "Cost of Goods Sold / Cost of Revenue",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "cost of goods sold", "cost of sales", "cogs", "cost of revenue",
            "cost of revenues", "direct costs", "direct operating costs",
            "cost of products sold", "cost of services", "direct materials and labor"
        ]
    },
    "gross_profit": {
        "canonical_label": "Gross Profit",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "gross profit", "gross margin", "gross income", "gross profit / (loss)"
        ]
    },
    "research_and_development": {
        "canonical_label": "Research and Development (R&D)",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "research and development", "r&d", "research & development",
            "r&d expense", "technology and development"
        ]
    },
    "selling_general_and_administrative": {
        "canonical_label": "Selling, General and Administrative (SG&A)",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "selling, general and administrative", "sg&a", "sga",
            "selling general & administrative", "sales and marketing",
            "general and administrative", "g&a", "administrative expenses",
            "operating and administrative expenses", "selling and marketing expenses"
        ]
    },
    "operating_expenses": {
        "canonical_label": "Total Operating Expenses",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "operating expenses", "total operating expenses", "operating costs",
            "total operating costs", "total expenses from operations"
        ]
    },
    "operating_income": {
        "canonical_label": "Operating Income (EBIT)",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "operating income", "operating profit", "operating loss",
            "income from operations", "operating profit / (loss)",
            "ebit", "profit from operations", "operating earnings"
        ]
    },
    "interest_expense": {
        "canonical_label": "Interest Expense / Finance Costs",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "interest expense", "finance costs", "financing costs",
            "interest and financing fees", "interest paid", "finance charges"
        ]
    },
    "interest_income": {
        "canonical_label": "Interest Income / Finance Income",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "interest income", "finance income", "investment income",
            "interest and dividend income"
        ]
    },
    "income_before_tax": {
        "canonical_label": "Income / Profit Before Tax (EBT)",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "income before taxes", "income before tax", "earnings before taxes",
            "ebt", "profit before tax", "profit / (loss) before tax",
            "profit before taxation", "income before provision for income taxes"
        ]
    },
    "income_tax_expense": {
        "canonical_label": "Income Tax Expense",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "income tax expense", "provision for income taxes", "taxation",
            "income tax", "tax expense", "provision for taxes", "taxes on income"
        ]
    },
    "net_income": {
        "canonical_label": "Net Income / Net Profit",
        "category": StatementCategory.INCOME_STATEMENT,
        "aliases": [
            "net income", "net earnings", "net profit", "profit for the year",
            "profit / (loss) for the period", "net profit / (loss) after tax",
            "profit after tax", "net income attributable to company", "bottom line"
        ]
    },

    # ------------------ BALANCE SHEET: ASSETS ------------------
    "cash_and_cash_equivalents": {
        "canonical_label": "Cash and Cash Equivalents",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "cash and cash equivalents", "cash at bank and in hand",
            "cash and equivalents", "cash & cash equivalents",
            "cash & equivalents", "cash and short-term investments",
            "bank balances", "cash and bank balances", "cash"
        ]
    },
    "marketable_securities": {
        "canonical_label": "Marketable Securities / Short-Term Investments",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "marketable securities", "short-term investments",
            "short term financial assets", "current investments"
        ]
    },
    "accounts_receivable": {
        "canonical_label": "Accounts Receivable / Trade Receivables",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "accounts receivable", "trade receivables", "trade and other receivables",
            "receivables from customers", "debtors", "trade debtors",
            "net accounts receivable"
        ]
    },
    "inventory": {
        "canonical_label": "Inventories",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "inventory", "inventories", "stock", "stock and work in progress",
            "merchandise inventory", "finished goods", "raw materials"
        ]
    },
    "prepaid_expenses": {
        "canonical_label": "Prepaid Expenses and Other Current Assets",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "prepaid expenses", "prepayments and accrued income",
            "other current assets", "prepayments", "advance payments"
        ]
    },
    "total_current_assets": {
        "canonical_label": "Total Current Assets",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "total current assets", "current assets", "total current asset"
        ]
    },
    "property_plant_equipment": {
        "canonical_label": "Property, Plant and Equipment (PPE)",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "property, plant and equipment", "property, plant & equipment",
            "ppe", "fixed assets", "tangible fixed assets", "tangible assets",
            "plant, property and equipment", "net ppe"
        ]
    },
    "goodwill_and_intangibles": {
        "canonical_label": "Goodwill and Intangible Assets",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "goodwill", "intangible assets", "goodwill and intangible assets",
            "intangibles", "intellectual property", "patents and trademarks"
        ]
    },
    "long_term_investments": {
        "canonical_label": "Long-Term Investments",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "long-term investments", "non-current investments",
            "investments in subsidiaries", "financial assets at fair value"
        ]
    },
    "total_non_current_assets": {
        "canonical_label": "Total Non-Current Assets",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "total non-current assets", "non-current assets",
            "total fixed assets", "long-term assets"
        ]
    },
    "total_assets": {
        "canonical_label": "Total Assets",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "total assets", "total asset"
        ]
    },

    # ------------------ BALANCE SHEET: LIABILITIES ------------------
    "accounts_payable": {
        "canonical_label": "Accounts Payable / Trade Payables",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "accounts payable", "trade payables", "trade and other payables",
            "creditors: amounts falling due within one year", "trade creditors",
            "bills payable"
        ]
    },
    "short_term_debt": {
        "canonical_label": "Short-Term Debt / Borrowings",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "short-term debt", "current portion of long-term debt",
            "short term debt", "short-term borrowings", "bank overdrafts",
            "current borrowings", "current lease liabilities"
        ]
    },
    "accrued_liabilities": {
        "canonical_label": "Accrued Liabilities and Other Current Liabilities",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "accrued liabilities", "accrued expenses", "other current liabilities",
            "accruals and deferred income", "taxes payable"
        ]
    },
    "total_current_liabilities": {
        "canonical_label": "Total Current Liabilities",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "total current liabilities", "current liabilities"
        ]
    },
    "long_term_debt": {
        "canonical_label": "Long-Term Debt / Borrowings",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "long-term debt", "long term debt", "borrowings",
            "loans and borrowings", "non-current borrowings",
            "creditors: amounts falling due after more than one year",
            "term loans", "senior notes", "non-current lease liabilities"
        ]
    },
    "deferred_tax_liabilities": {
        "canonical_label": "Deferred Tax Liabilities / Provisions",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "deferred tax liabilities", "deferred tax liability",
            "deferred revenue (non-current)", "provisions for liabilities"
        ]
    },
    "total_non_current_liabilities": {
        "canonical_label": "Total Non-Current Liabilities",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "total non-current liabilities", "non-current liabilities",
            "total long-term liabilities", "long-term liabilities"
        ]
    },
    "total_liabilities": {
        "canonical_label": "Total Liabilities",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "total liabilities", "total liability"
        ]
    },

    # ------------------ BALANCE SHEET: EQUITY ------------------
    "common_stock": {
        "canonical_label": "Common Stock / Share Capital",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "common stock", "share capital", "ordinary shares",
            "capital stock", "called up share capital", "common shares"
        ]
    },
    "additional_paid_in_capital": {
        "canonical_label": "Additional Paid-In Capital / Share Premium",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "additional paid-in capital", "additional paid in capital",
            "share premium", "capital reserve", "apic"
        ]
    },
    "retained_earnings": {
        "canonical_label": "Retained Earnings / Accumulated Deficit",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "retained earnings", "accumulated deficit", "retained profit",
            "accumulated earnings", "profit and loss account reserve"
        ]
    },
    "total_stockholders_equity": {
        "canonical_label": "Total Stockholders' / Shareholders' Equity",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "total stockholders' equity", "total shareholders' equity",
            "total equity", "shareholders' funds", "total stockholders equity",
            "total shareholders equity", "equity attributable to owners"
        ]
    },
    "total_liabilities_and_equity": {
        "canonical_label": "Total Liabilities and Equity",
        "category": StatementCategory.BALANCE_SHEET,
        "aliases": [
            "total liabilities and stockholders' equity",
            "total liabilities and equity",
            "total liabilities and shareholders' equity",
            "total equity and liabilities"
        ]
    }
}
