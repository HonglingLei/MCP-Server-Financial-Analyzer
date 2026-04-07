"""Tools for financial statement data (income statement, balance sheet, cash flow)."""

import json

import pandas as pd

from financial_analyzer.app import mcp
from financial_analyzer.data.yahoo_finance import fetch_earnings, fetch_financials


def _df_to_json(df: pd.DataFrame | None) -> dict:
    if df is None or df.empty:
        return {}
    return json.loads(df.to_json(orient="columns", date_format="iso"))


def _get_financial_statement(ticker: str, period: str, key_prefix: str, output_field: str) -> str:
    try:
        key = f"{key_prefix}_annual" if period == "annual" else f"{key_prefix}_quarterly"
        data = fetch_financials(ticker, keys=[key])
        result = _df_to_json(data.get(key))
        if not result:
            return f"No {output_field.replace('_', ' ')} data found for '{ticker}'."
        return json.dumps({"ticker": ticker.upper(), "period": period, output_field: result}, indent=2)
    except Exception as e:
        return f"Error fetching {output_field.replace('_', ' ')} for '{ticker}': {type(e).__name__}: {e}"


@mcp.tool()
def get_income_statement(ticker: str, period: str = "annual") -> str:
    """Get income statement data (revenue, gross profit, EBITDA, net income, EPS).

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
        period: 'annual' or 'quarterly'
    """
    return _get_financial_statement(ticker, period, "income_stmt", "income_statement")


@mcp.tool()
def get_balance_sheet(ticker: str, period: str = "annual") -> str:
    """Get balance sheet data (assets, liabilities, equity, debt).

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
        period: 'annual' or 'quarterly'
    """
    return _get_financial_statement(ticker, period, "balance_sheet", "balance_sheet")


@mcp.tool()
def get_cash_flow(ticker: str, period: str = "annual") -> str:
    """Get cash flow statement (operating, investing, financing, free cash flow).

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
        period: 'annual' or 'quarterly'
    """
    return _get_financial_statement(ticker, period, "cash_flow", "cash_flow")


@mcp.tool()
def get_earnings_history(ticker: str) -> str:
    """Get earnings history showing EPS estimates vs actuals and surprise percentages.

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
    """
    try:
        data = fetch_earnings(ticker)
        if not data:
            return f"No earnings history found for '{ticker}'."
        return json.dumps({"ticker": ticker.upper(), "earnings_history": data}, indent=2)
    except Exception as e:
        return f"Error fetching earnings for '{ticker}': {type(e).__name__}: {e}"
