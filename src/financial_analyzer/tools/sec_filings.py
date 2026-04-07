"""Tools for SEC EDGAR filings (10-K, 10-Q, 8-K, etc.)."""

import json

from financial_analyzer.app import mcp
from financial_analyzer.data import edgar_client


@mcp.tool()
def search_sec_filings(
    ticker: str,
    form_type: str = "10-K",
    limit: int = 5,
) -> str:
    """Search for SEC filings for a company.

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
        form_type: Filing type - '10-K', '10-Q', '8-K', 'DEF 14A', 'S-1', etc.
        limit: Maximum number of filings to return (1-20)
    """
    try:
        limit = max(1, min(20, limit))
        filings = edgar_client.get_filings(ticker, form_type=form_type, limit=limit)
        if not filings:
            return f"No {form_type} filings found for '{ticker}'."
        return json.dumps(
            {"ticker": ticker.upper(), "form_type": form_type, "filings": filings},
            indent=2,
        )
    except Exception as e:
        return f"Error searching filings for '{ticker}': {type(e).__name__}: {e}"


@mcp.tool()
def get_filing_sections(
    ticker: str,
    form_type: str = "10-K",
    filing_date: str = "",
    sections: str = "all",
) -> str:
    """Retrieve key sections from an SEC filing as markdown text.

    For 10-K filings the important sections are: business, risk_factors, mda
    (Management Discussion & Analysis), financials.

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
        form_type: Filing type - '10-K' or '10-Q'
        filing_date: Exact filing date YYYY-MM-DD; leave empty for most recent
        sections: Comma-separated section names to retrieve, or 'all' for a summary.
                  Common values: 'business', 'risk_factors', 'mda'
    """
    try:
        filing = edgar_client.get_filing_by_date(ticker, form_type, filing_date)
        if filing is None:
            return f"No {form_type} filing found for '{ticker}' on '{filing_date}'."

        meta = {
            "ticker": ticker.upper(),
            "form": filing.form,
            "filing_date": str(filing.filing_date),
            "period_of_report": str(filing.period_of_report) if filing.period_of_report else None,
            "accession_number": filing.accession_number,
            "filing_url": filing.filing_url,
        }

        if sections == "all":
            # Return a concise markdown summary (first ~3000 chars to avoid huge payloads)
            try:
                text = filing.markdown()
                if text and len(text) > 4000:
                    text = text[:4000] + "\n\n...[truncated — request specific sections for full text]"
            except Exception:
                text = "[Markdown not available for this filing]"
            return json.dumps({"metadata": meta, "content": text}, indent=2)

        # Retrieve a structured object (TenK / TenQ) if available
        try:
            obj = filing.obj()
        except Exception:
            obj = None

        content: dict[str, str] = {}
        for section in [s.strip() for s in sections.split(",")]:
            if obj is not None and hasattr(obj, section):
                raw = getattr(obj, section)
                if raw is None:
                    content[section] = "[Not available]"
                else:
                    text = str(raw)
                    if len(text) > 3000:
                        text = text[:3000] + "\n...[truncated]"
                    content[section] = text
            else:
                content[section] = f"[Section '{section}' not found in this filing type]"

        return json.dumps({"metadata": meta, "sections": content}, indent=2)
    except Exception as e:
        return f"Error retrieving filing for '{ticker}': {type(e).__name__}: {e}"


@mcp.tool()
def get_company_facts(ticker: str) -> str:
    """Get basic company facts from SEC EDGAR (CIK, name, registered tickers).

    Also retrieves TTM (trailing twelve months) revenue and net income from
    the company's XBRL filings when available.

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
    """
    try:
        facts = edgar_client.get_company_facts(ticker)
        if not facts:
            return f"No EDGAR data found for '{ticker}'."

        # Enrich with TTM financials from edgar
        try:
            fin = edgar_client.get_financials(ticker)
            if fin:
                facts["ttm_revenue"] = fin.get_revenue()
                facts["ttm_net_income"] = fin.get_net_income()
                facts["total_assets"] = fin.get_total_assets()
                facts["total_liabilities"] = fin.get_total_liabilities()
                facts["stockholders_equity"] = fin.get_stockholders_equity()
                facts["operating_cash_flow"] = fin.get_operating_cash_flow()
                facts["free_cash_flow"] = fin.get_free_cash_flow()
                facts["shares_outstanding"] = fin.get_shares_outstanding_diluted()
        except Exception:
            pass  # If XBRL data unavailable, return what we have

        # Clean up non-serialisable values
        clean: dict = {}
        for k, v in facts.items():
            if v is None:
                continue
            try:
                json.dumps(v)
                clean[k] = v
            except (TypeError, ValueError):
                clean[k] = str(v)

        return json.dumps(clean, indent=2)
    except Exception as e:
        return f"Error fetching company facts for '{ticker}': {type(e).__name__}: {e}"
