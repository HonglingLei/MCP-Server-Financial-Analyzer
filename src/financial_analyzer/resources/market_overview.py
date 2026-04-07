"""MCP resources for market-level data."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from financial_analyzer.app import mcp
from financial_analyzer.data.yahoo_finance import fetch_info

_INDEX_SYMBOLS = {
    "S&P 500": "^GSPC",
    "NASDAQ Composite": "^IXIC",
    "Dow Jones": "^DJI",
    "Russell 2000": "^RUT",
    "VIX": "^VIX",
    "10Y Treasury": "^TNX",
}

_SECTOR_ETFS = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
}


def _fetch_index(name: str, symbol: str) -> tuple[str, dict]:
    try:
        info = fetch_info(symbol)
        return name, {
            "symbol": symbol,
            "price": info.get("regularMarketPrice") or info.get("currentPrice"),
            "change": info.get("regularMarketChange"),
            "change_pct": info.get("regularMarketChangePercent"),
            "previous_close": info.get("regularMarketPreviousClose"),
        }
    except Exception as e:
        return name, {"symbol": symbol, "error": str(e)}


def _fetch_sector(sector: str, symbol: str) -> tuple[str, dict]:
    try:
        info = fetch_info(symbol)
        return sector, {
            "etf": symbol,
            "price": info.get("regularMarketPrice") or info.get("currentPrice"),
            "change_pct": info.get("regularMarketChangePercent"),
            "ytd_return": info.get("ytdReturn"),
        }
    except Exception as e:
        return sector, {"etf": symbol, "error": str(e)}


@mcp.resource("market://overview")
def market_overview() -> str:
    """Current levels of major US market indices and volatility indicators."""
    results = {}
    with ThreadPoolExecutor(max_workers=len(_INDEX_SYMBOLS)) as pool:
        futures = {pool.submit(_fetch_index, name, symbol): name for name, symbol in _INDEX_SYMBOLS.items()}
        for fut in as_completed(futures):
            name, data = fut.result()
            results[name] = data
    return json.dumps(results, indent=2)


@mcp.resource("market://sectors")
def sector_performance() -> str:
    """Daily performance of major US stock market sectors via SPDR ETFs."""
    results = {}
    with ThreadPoolExecutor(max_workers=len(_SECTOR_ETFS)) as pool:
        futures = {pool.submit(_fetch_sector, sector, symbol): sector for sector, symbol in _SECTOR_ETFS.items()}
        for fut in as_completed(futures):
            sector, data = fut.result()
            results[sector] = data
    return json.dumps(results, indent=2)
