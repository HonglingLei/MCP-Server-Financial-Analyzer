"""Wrapper around edgartools for SEC EDGAR data."""

import os
from typing import Any

import edgar

# EDGAR requires a User-Agent identifying the requester.
# Set EDGAR_IDENTITY in .env as "Your Name your@email.com"
_identity = os.getenv("EDGAR_IDENTITY", "Financial Analyzer mcp-financial-analyzer@example.com")
edgar.set_identity(_identity)


def get_company(ticker: str) -> edgar.Company:
    return edgar.Company(ticker.upper())


def get_filings(ticker: str, form_type: str = "10-K", limit: int = 5) -> list[dict[str, Any]]:
    company = get_company(ticker)
    filings = company.get_filings(form=form_type)
    results = []
    for i, f in enumerate(filings):
        if i >= limit:
            break
        results.append(
            {
                "form": f.form,
                "filing_date": str(f.filing_date),
                "period_of_report": str(f.period_of_report) if f.period_of_report else None,
                "accession_number": f.accession_number,
                "filing_url": f.filing_url,
            }
        )
    return results


def get_filing_by_date(ticker: str, form_type: str, filing_date: str):
    """Return the filing matching the given date (YYYY-MM-DD), or the most recent."""
    company = get_company(ticker)
    filings = company.get_filings(form=form_type)
    first = None
    for f in filings:
        if first is None:
            first = f
        if str(f.filing_date) == filing_date:
            return f
    return first


def get_company_facts(ticker: str) -> dict:
    company = get_company(ticker)
    facts = company.get_facts()
    if facts is None:
        return {}
    # facts is a CompanyFacts object; convert to a summary dict
    summary: dict[str, Any] = {
        "cik": company.cik,
        "name": company.name,
        "tickers": company.tickers,
    }
    return summary


def get_financials(ticker: str):
    """Return edgar Financials object (wraps XBRL data from latest 10-K)."""
    company = get_company(ticker)
    return company.get_financials()
