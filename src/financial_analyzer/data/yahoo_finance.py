"""Thin wrapper around yfinance to centralise all Yahoo Finance calls."""

import json

import pandas as pd
import yfinance as yf

_FINANCIAL_KEYS: dict = {
    "income_stmt_annual":       lambda t: t.income_stmt,
    "income_stmt_quarterly":    lambda t: t.quarterly_income_stmt,
    "balance_sheet_annual":     lambda t: t.balance_sheet,
    "balance_sheet_quarterly":  lambda t: t.quarterly_balance_sheet,
    "cash_flow_annual":         lambda t: t.cash_flow,
    "cash_flow_quarterly":      lambda t: t.quarterly_cash_flow,
}


def df_to_dict(df: pd.DataFrame) -> dict:
    """Convert a DataFrame to a JSON-serialisable dict (orient=index: rows as outer keys)."""
    return json.loads(df.to_json(orient="index", date_format="iso", default_handler=str))


def get_ticker(symbol: str) -> yf.Ticker:
    return yf.Ticker(symbol.upper())


def fetch_info(symbol: str) -> dict:
    t = get_ticker(symbol)
    return t.info or {}


def fetch_history(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    t = get_ticker(symbol)
    return t.history(period=period, interval=interval)


def fetch_financials(symbol: str, keys: list[str] | None = None) -> dict[str, pd.DataFrame | None]:
    """Fetch financial statements. Pass *keys* to request only what you need."""
    t = get_ticker(symbol)
    wanted = keys if keys else list(_FINANCIAL_KEYS)
    return {k: _FINANCIAL_KEYS[k](t) for k in wanted}


def fetch_earnings(symbol: str) -> dict:
    t = get_ticker(symbol)
    hist = t.earnings_history
    if hist is None or hist.empty:
        return {}
    return df_to_dict(hist)
