"""
Generates 5 realistic sample financial statements (3 PDFs, 2 XLSXs)
across multiple industries and accounting conventions to validate the DRP-1 pipeline.
"""

import os
from pathlib import Path
from fpdf import FPDF
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

RAW_DATA_DIR = Path("data/raw")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def create_pdf_statement(filename: str, company: str, period: str, currency: str, unit: str,
                         bs_data: list, is_data: list, notes: list):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Page 1: Financial Tables
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, company, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, f"Consolidated Financial Statements - {period}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, f"Currency: {currency} (Amounts in {unit})", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Balance Sheet Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "CONSOLIDATED BALANCE SHEET", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    headers = ["Line Item", "2024", "2023"]
    col_w = [110, 40, 40]
    for h, w in zip(headers, col_w):
        pdf.cell(w, 6, h, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for row in bs_data:
        is_bold = any(k in row[0].lower() for k in ["total", "equity and liabilities"])
        if is_bold:
            pdf.set_font("Helvetica", "B", 8)
        else:
            pdf.set_font("Helvetica", "", 8)
        for val, w in zip(row, col_w):
            pdf.cell(w, 5.5, str(val), border=1)
        pdf.ln()

    pdf.ln(4)

    # Income Statement Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "CONSOLIDATED STATEMENT OF OPERATIONS (INCOME STATEMENT)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    for h, w in zip(headers, col_w):
        pdf.cell(w, 6, h, border=1)
    pdf.ln()

    for row in is_data:
        is_bold = any(k in row[0].lower() for k in ["gross profit", "operating income", "net income", "profit before tax"])
        if is_bold:
            pdf.set_font("Helvetica", "B", 8)
        else:
            pdf.set_font("Helvetica", "", 8)
        for val, w in zip(row, col_w):
            pdf.cell(w, 5.5, str(val), border=1)
        pdf.ln()

    # Page 2+: Notes to Accounts
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, f"{company} - Notes to the Consolidated Financial Statements", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, f"Fiscal Period Ended December 31, {period}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for note in notes:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, note["title"], new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 4.5, note["body"])
        pdf.ln(3)

    out_file = RAW_DATA_DIR / filename
    pdf.output(str(out_file))
    print(f"Created: {out_file}")


def create_excel_statement(filename: str, company: str, period: str, currency: str, unit: str,
                           bs_data: list, is_data: list, notes: list):
    wb = openpyxl.Workbook()
    # Sheet 1: Balance Sheet
    ws_bs = wb.active
    ws_bs.title = "Balance Sheet"
    
    ws_bs.append([company])
    ws_bs.append([f"Balance Sheet as of December 31, {period}"])
    ws_bs.append([f"Currency: {currency} (in {unit})"])
    ws_bs.append([])
    ws_bs.append(["Line Item", "2024", "2023"])

    for row in bs_data:
        ws_bs.append(row)

    # Sheet 2: Income Statement
    ws_is = wb.create_sheet(title="Income Statement")
    ws_is.append([company])
    ws_is.append([f"Statement of Profit and Loss for Year Ended {period}"])
    ws_is.append([f"Currency: {currency} (in {unit})"])
    ws_is.append([])
    ws_is.append(["Line Item", "2024", "2023"])

    for row in is_data:
        ws_is.append(row)

    # Sheet 3: Notes & Disclosures
    ws_notes = wb.create_sheet(title="Notes to Accounts")
    ws_notes.append([company, f"Notes to Financial Statements ({period})"])
    ws_notes.append([])
    for note in notes:
        ws_notes.append([note["title"]])
        ws_notes.append([note["body"]])
        ws_notes.append([])

    # Basic formatting
    header_fill = PatternFill(start_color="E0EBF5", end_color="E0EBF5", fill_type="solid")
    title_font = Font(size=12, bold=True)
    header_font = Font(size=10, bold=True)

    for ws in [ws_bs, ws_is]:
        ws["A1"].font = title_font
        ws["A2"].font = Font(size=10, italic=True)
        for col in ["A", "B", "C"]:
            ws[f"{col}5"].font = header_font
            ws[f"{col}5"].fill = header_fill
        ws.column_dimensions["A"].width = 45
        ws.column_dimensions["B"].width = 18
        ws.column_dimensions["C"].width = 18

    ws_notes.column_dimensions["A"].width = 100

    out_file = RAW_DATA_DIR / filename
    wb.save(out_file)
    print(f"Created: {out_file}")


def generate_all_samples():
    print("Generating 5 sample financial statements...")

    # -------------------------------------------------------------
    # SAMPLE 1 (PDF): TechVanguard Software Inc. (SaaS)
    # -------------------------------------------------------------
    bs_1 = [
        ["Cash and cash equivalents", "48,500", "35,200"],
        ["Marketable securities", "15,000", "12,000"],
        ["Accounts receivable", "22,300", "18,900"],
        ["Prepaid expenses", "4,200", "3,800"],
        ["Total Current Assets", "90,000", "69,900"],
        ["Property, plant & equipment", "12,400", "10,500"],
        ["Goodwill and intangible assets", "38,000", "40,000"],
        ["Total Non-Current Assets", "50,400", "50,500"],
        ["Total Assets", "140,400", "120,400"],
        ["Accounts payable", "8,500", "7,200"],
        ["Short-term debt", "5,000", "4,000"],
        ["Accrued liabilities", "14,500", "11,800"],
        ["Total Current Liabilities", "28,000", "23,000"],
        ["Long-term debt", "30,000", "35,000"],
        ["Total Non-Current Liabilities", "30,000", "35,000"],
        ["Total Liabilities", "58,000", "58,000"],
        ["Common stock", "1,000", "1,000"],
        ["Retained earnings", "81,400", "61,400"],
        ["Total Stockholders Equity", "82,400", "62,400"],
        ["Total Liabilities and Stockholders Equity", "140,400", "120,400"]
    ]
    is_1 = [
        ["Total Revenue", "125,000", "98,000"],
        ["Cost of Goods Sold", "31,250", "26,460"],
        ["Gross Profit", "93,750", "71,540"],
        ["Research and Development", "28,000", "22,500"],
        ["Selling, General and Administrative", "35,000", "28,000"],
        ["Total Operating Expenses", "63,000", "50,500"],
        ["Operating Income", "30,750", "21,040"],
        ["Interest Expense", "1,800", "2,100"],
        ["Income Before Taxes", "28,950", "18,940"],
        ["Income Tax Expense", "6,080", "3,980"],
        ["Net Income", "22,870", "14,960"]
    ]
    notes_1 = [
        {
            "title": "Note 1 - Organization and Summary of Significant Accounting Policies",
            "body": (
                "TechVanguard Software Inc. is a provider of cloud-based enterprise intelligence software. "
                "The accompanying consolidated financial statements have been prepared in conformity with US GAAP. "
                "Revenue is recognized pursuant to ASC 606 when control of promised software services is transferred to customers, "
                "typically ratably over annual or multi-year subscription terms. Trade receivables are carried at face value less allowance "
                "for credit losses. Capitalized software development costs are amortized on a straight-line basis over 3 years."
            )
        },
        {
            "title": "Note 2 - Operating Leases and Commitments",
            "body": (
                "The Company leases office facilities and data center capacity under non-cancelable operating leases expiring at various dates "
                "through 2029. As of December 31, 2024, operating lease liabilities were USD 8.4 million with a weighted-average remaining lease term "
                "of 4.2 years and a discount rate of 5.5%. Future minimum lease obligations are USD 2.5 million in 2025, USD 2.2 million in 2026, "
                "and USD 3.7 million thereafter."
            )
        },
        {
            "title": "Note 3 - Credit Facilities and Long-Term Debt",
            "body": (
                "As of December 31, 2024, the Company maintained a senior secured term loan facility with an outstanding principal of USD 30.0 million "
                "bearing interest at Term SOFR plus 2.25%. The credit agreement contains financial covenants requiring maintenance of a minimum "
                "fixed charge coverage ratio of 1.25x and maximum leverage ratio of 2.75x. The Company was in full compliance with all covenants."
            )
        },
        {
            "title": "Note 4 - Stock-Based Compensation",
            "body": (
                "The Company recognized stock-based compensation expense of USD 4.8 million for the year ended December 31, 2024. "
                "Restricted stock units (RSUs) vest over a four-year period with a 25% cliff at one year and quarterly vesting thereafter. "
                "Unrecognized compensation expense related to unvested awards was USD 7.2 million, expected to be recognized over 2.6 years."
            )
        }
    ]
    create_pdf_statement("Sample_1_TechVanguard_FY24.pdf", "TechVanguard Software Inc.", "FY2024", "USD", "thousands", bs_1, is_1, notes_1)

    # -------------------------------------------------------------
    # SAMPLE 2 (XLSX): Apex Retail Corporation
    # -------------------------------------------------------------
    bs_2 = [
        ["Cash and bank balances", "18,200", "14,500"],
        ["Inventories", "64,500", "58,200"],
        ["Trade and other receivables", "9,800", "8,600"],
        ["Prepayments", "3,100", "2,900"],
        ["Total Current Assets", "95,600", "84,200"],
        ["Tangible fixed assets", "82,400", "80,100"],
        ["Goodwill", "12,000", "12,000"],
        ["Total Non-Current Assets", "94,400", "92,100"],
        ["Total Assets", "190,000", "176,300"],
        ["Trade payables", "34,200", "31,000"],
        ["Current borrowings", "12,000", "15,000"],
        ["Accruals and deferred income", "8,500", "7,800"],
        ["Total Current Liabilities", "54,700", "53,800"],
        ["Loans and borrowings", "45,000", "48,000"],
        ["Total Non-Current Liabilities", "45,000", "48,000"],
        ["Total Liabilities", "99,700", "101,800"],
        ["Called up share capital", "20,000", "20,000"],
        ["Retained profit", "70,300", "54,500"],
        ["Total Shareholders' Equity", "90,300", "74,500"],
        ["Total Liabilities and Equity", "190,000", "176,300"]
    ]
    is_2 = [
        ["Turnover", "240,000", "215,000"],
        ["Cost of sales", "156,000", "141,900"],
        ["Gross Profit", "84,000", "73,100"],
        ["Administrative expenses", "46,500", "42,000"],
        ["Total Operating Expenses", "46,500", "42,000"],
        ["Operating Profit", "37,500", "31,100"],
        ["Finance costs", "3,200", "3,600"],
        ["Profit Before Tax", "34,300", "27,500"],
        ["Taxation", "7,500", "6,050"],
        ["Profit for the year", "26,800", "21,450"]
    ]
    notes_2 = [
        {
            "title": "Note 1: Accounting Convention and Basis of Preparation",
            "body": (
                "The financial statements of Apex Retail Corporation have been prepared under the historical cost convention "
                "in accordance with applicable financial reporting standards. Turnover comprises retail merchandise sales and online deliveries, "
                "net of discounts and returns provisions."
            )
        },
        {
            "title": "Note 2: Inventories and Stock Valuation",
            "body": (
                "Inventories are stated at the lower of cost and net realizable value using the First-In, First-Out (FIFO) method. "
                "As of December 31, 2024, finished merchandise was USD 58.1 million and goods in transit totaled USD 6.4 million. "
                "A reserve of USD 2.1 million was maintained for obsolete and slow-moving retail inventory."
            )
        },
        {
            "title": "Note 3: Tangible Fixed Assets and Depreciation",
            "body": (
                "Tangible fixed assets are stated at cost less accumulated depreciation. Store fixtures and equipment are depreciated over "
                "5 to 10 years, and warehouse facilities over 25 years on a straight-line basis. Depreciation charge for 2024 was USD 9.4 million."
            )
        }
    ]
    create_excel_statement("Sample_2_ApexRetail_FY24.xlsx", "Apex Retail Corporation", "FY2024", "USD", "thousands", bs_2, is_2, notes_2)

    # -------------------------------------------------------------
    # SAMPLE 3 (PDF): BioHealth Diagnostics Inc.
    # -------------------------------------------------------------
    bs_3 = [
        ["Cash and cash equivalents", "24,600", "19,800"],
        ["Trade receivables", "14,200", "11,500"],
        ["Inventories", "8,100", "7,400"],
        ["Other current assets", "2,100", "1,800"],
        ["Total Current Assets", "49,000", "40,500"],
        ["Property, plant and equipment", "36,000", "32,000"],
        ["Intangible assets", "28,500", "30,000"],
        ["Total Non-Current Assets", "64,500", "62,000"],
        ["Total Assets", "113,500", "102,500"],
        ["Trade payables", "9,400", "8,100"],
        ["Short-term borrowings", "4,000", "6,000"],
        ["Accrued expenses", "5,600", "4,900"],
        ["Total Current Liabilities", "19,000", "19,000"],
        ["Long-term debt", "22,000", "25,000"],
        ["Deferred tax liabilities", "3,500", "3,200"],
        ["Total Non-Current Liabilities", "25,500", "28,200"],
        ["Total Liabilities", "44,500", "47,200"],
        ["Share capital", "15,000", "15,000"],
        ["Retained earnings", "54,000", "40,300"],
        ["Total Shareholders Equity", "69,000", "55,300"],
        ["Total Liabilities and Shareholders Equity", "113,500", "102,500"]
    ]
    is_3 = [
        ["Revenue", "86,400", "72,000"],
        ["Cost of sales", "28,500", "24,480"],
        ["Gross Profit", "57,900", "47,520"],
        ["Research and development", "19,500", "16,200"],
        ["Selling and marketing", "14,800", "12,960"],
        ["General and administrative", "8,200", "7,200"],
        ["Total Operating Expenses", "42,500", "36,360"],
        ["Operating Profit", "15,400", "11,160"],
        ["Finance costs", "1,200", "1,450"],
        ["Profit Before Tax", "14,200", "9,710"],
        ["Taxation", "2,840", "1,940"],
        ["Net Profit", "11,360", "7,770"]
    ]
    notes_3 = [
        {
            "title": "Note 1 - Principal Accounting Policies and Regulatory Context",
            "body": (
                "BioHealth Diagnostics Inc. develops clinical molecular diagnostic kits. "
                "The financial statements comply with International Financial Reporting Standards (IFRS). "
                "Revenues from reagent diagnostic kit sales are recognized at point of delivery, whereas instrument placements "
                "are evaluated under multi-component contract criteria."
            )
        },
        {
            "title": "Note 2 - Government Grants and Collaborative Research",
            "body": (
                "During FY2024, the entity received GBP 2.4 million in government grants for oncology diagnostic development. "
                "Grants related to income are recognized in the statement of profit and loss as a reduction of research and development expense "
                "in the period in which the associated research costs are incurred."
            )
        },
        {
            "title": "Note 3 - Contingent Liabilities and IP Licensing",
            "body": (
                "The company is engaged in cross-licensing agreements with two academic research institutions. Contingent royalty obligations "
                "range between 2.5% and 4.0% of net commercial kit revenues. There are no ongoing patent infringement disputes or litigation claims."
            )
        }
    ]
    create_pdf_statement("Sample_3_BioHealth_Diagnostics_FY24.pdf", "BioHealth Diagnostics Inc.", "FY2024", "GBP", "thousands", bs_3, is_3, notes_3)

    # -------------------------------------------------------------
    # SAMPLE 4 (XLSX): Precision Manufacturing Group
    # -------------------------------------------------------------
    bs_4 = [
        ["Cash and cash equivalents", "32,000", "28,000"],
        ["Trade and other receivables", "45,000", "41,000"],
        ["Inventories", "52,000", "48,000"],
        ["Total Current Assets", "129,000", "117,000"],
        ["Property, plant & equipment", "140,000", "135,000"],
        ["Goodwill and intangible assets", "24,000", "25,000"],
        ["Total Non-Current Assets", "164,000", "160,000"],
        ["Total Assets", "293,000", "277,000"],
        ["Trade payables", "38,000", "35,000"],
        ["Short-term borrowings", "15,000", "18,000"],
        ["Other current liabilities", "12,000", "10,000"],
        ["Total Current Liabilities", "65,000", "63,000"],
        ["Long term debt", "70,000", "75,000"],
        ["Total Non-Current Liabilities", "70,000", "75,000"],
        ["Total Liabilities", "135,000", "138,000"],
        ["Share capital", "50,000", "50,000"],
        ["Retained earnings", "108,000", "89,000"],
        ["Total Shareholders Equity", "158,000", "139,000"],
        ["Total Liabilities and Equity", "293,000", "277,000"]
    ]
    is_4 = [
        ["Net Sales", "310,000", "285,000"],
        ["Cost of products sold", "217,000", "202,350"],
        ["Gross Margin", "93,000", "82,650"],
        ["Selling, general & administrative", "42,000", "38,500"],
        ["Total Operating Costs", "42,000", "38,500"],
        ["Operating Income", "51,000", "44,150"],
        ["Interest expense", "4,800", "5,200"],
        ["Profit before taxation", "46,200", "38,950"],
        ["Income tax expense", "10,600", "8,950"],
        ["Net Profit", "35,600", "30,000"]
    ]
    notes_4 = [
        {
            "title": "Note 1: Long-Term Manufacturing Contracts and Revenue",
            "body": (
                "Precision Manufacturing Group applies IFRS 15 for heavy machinery build contracts. Revenue is recognized over time "
                "using the input cost-to-cost percentage-of-completion method. Contract assets of EUR 14.2 million represent unbilled work "
                "in progress under long-cycle industrial fabrication agreements."
            )
        },
        {
            "title": "Note 2: Property, Plant and Equipment and Capital Commitments",
            "body": (
                "Capital expenditure commitments contracted for at year-end but not yet incurred were EUR 8.5 million for automated CNC machining lines. "
                "Plant and machinery is depreciated using the straight-line method over 7 to 15 years."
            )
        },
        {
            "title": "Note 3: Defined Benefit Pension Liabilities",
            "body": (
                "The Group operates a defined benefit pension scheme covering European factory personnel. The present value of funded obligations "
                "was EUR 42.0 million against plan assets of EUR 39.2 million, resulting in a net recognized deficit of EUR 2.8 million."
            )
        }
    ]
    create_excel_statement("Sample_4_PrecisionManufacturing_FY24.xlsx", "Precision Manufacturing Group", "FY2024", "EUR", "thousands", bs_4, is_4, notes_4)

    # -------------------------------------------------------------
    # SAMPLE 5 (PDF): Clean Energy Solutions Corp
    # -------------------------------------------------------------
    bs_5 = [
        ["Cash and cash equivalents", "85.0", "62.0"],
        ["Accounts receivable", "42.0", "38.0"],
        ["Prepaid expenses", "8.0", "6.0"],
        ["Total Current Assets", "135.0", "106.0"],
        ["Property, plant and equipment", "520.0", "480.0"],
        ["Intangible assets", "45.0", "45.0"],
        ["Total Non-Current Assets", "565.0", "525.0"],
        ["Total Assets", "700.0", "631.0"],
        ["Accounts payable", "35.0", "32.0"],
        ["Short-term borrowings", "20.0", "18.0"],
        ["Other current liabilities", "15.0", "12.0"],
        ["Total Current Liabilities", "70.0", "62.0"],
        ["Long-term debt", "280.0", "290.0"],
        ["Deferred tax liability", "40.0", "35.0"],
        ["Total Non-Current Liabilities", "320.0", "325.0"],
        ["Total Liabilities", "390.0", "387.0"],
        ["Common stock", "50.0", "50.0"],
        ["Retained earnings", "260.0", "194.0"],
        ["Total Stockholders Equity", "310.0", "244.0"],
        ["Total Liabilities and Stockholders Equity", "700.0", "631.0"]
    ]
    is_5 = [
        ["Total Revenue", "215.0", "180.0"],
        ["Cost of revenues", "105.0", "92.0"],
        ["Gross Profit", "110.0", "88.0"],
        ["Operating and administrative expenses", "32.0", "28.0"],
        ["Total Operating Expenses", "32.0", "28.0"],
        ["Operating Income", "78.0", "60.0"],
        ["Interest expense", "16.0", "17.5"],
        ["Income Before Taxes", "62.0", "42.5"],
        ["Income Tax Expense", "13.0", "8.5"],
        ["Net Income", "49.0", "34.0"]
    ]
    notes_5 = [
        {
            "title": "Note 1 - Operations and Renewable Asset Accounting",
            "body": (
                "Clean Energy Solutions Corp operates utility-scale solar and battery storage generation assets. "
                "Energy generation revenue is recognized based on power delivery under long-term Power Purchase Agreements (PPAs). "
                "Power generation infrastructure is depreciated over expected operational lives of 25 to 30 years."
            )
        },
        {
            "title": "Note 2 - Asset Retirement Obligations and Decommissioning",
            "body": (
                "The company records an asset retirement obligation (ARO) for contractual obligations to dismantle solar arrays "
                "and remediate leased agricultural land upon lease expiration. As of December 31, 2024, the discounted ARO liability was USD 18.5 million."
            )
        },
        {
            "title": "Note 3 - Green Bonds and Project Financing",
            "body": (
                "Long-term project debt comprises USD 180 million of senior secured green bonds due 2035 with a fixed coupon of 4.75%, "
                "and USD 100 million in commercial project bank loans. Debt service reserve accounts of USD 12.0 million are restricted and classified "
                "within non-current assets."
            )
        }
    ]
    create_pdf_statement("Sample_5_CleanEnergySolutions_FY24.pdf", "Clean Energy Solutions Corp", "FY2024", "USD", "millions", bs_5, is_5, notes_5)

    print("All 5 sample financial statements generated successfully in data/raw/")


if __name__ == "__main__":
    generate_all_samples()
