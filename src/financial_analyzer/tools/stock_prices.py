"""Tools for stock price and basic market data."""

import json

import pandas as pd

from financial_analyzer.app import mcp
from financial_analyzer.data.yahoo_finance import fetch_history, fetch_info


@mcp.tool()
def get_stock_price(ticker: str) -> str:
    """Get the current price and key market data for a stock.

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL', 'MSFT', 'TSLA'
    """
    try:
        info = fetch_info(ticker)
        if not info:
            return f"No data found for ticker '{ticker}'. Check the symbol is valid."

        result = {
            "ticker": ticker.upper(),
            "name": info.get("longName") or info.get("shortName"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "open": info.get("open") or info.get("regularMarketOpen"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "avg_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange"),
        }
        return json.dumps({k: v for k, v in result.items() if v is not None}, indent=2)
    except Exception as e:
        return f"Error fetching price for '{ticker}': {type(e).__name__}: {e}"


@mcp.tool()
def get_price_history(
    ticker: str,
    period: str = "1y",
    interval: str = "1d",
) -> str:
    """Get historical OHLCV price data for a stock.

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
        period: Time period - '1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd','max'
        interval: Data interval - '1m','2m','5m','15m','30m','60m','90m','1h','1d','5d','1wk','1mo','3mo'
    """
    try:
        df = fetch_history(ticker, period=period, interval=interval)
        if df.empty:
            return f"No price history found for '{ticker}' with period='{period}'."
        df = df.round(4)
        records = df.reset_index().to_dict(orient="records")
        # Serialise Timestamps
        for r in records:
            for k, v in r.items():
                if isinstance(v, pd.Timestamp):
                    r[k] = v.isoformat()
                elif isinstance(v, float) and v != v:
                    r[k] = None
        return json.dumps(
            {"ticker": ticker.upper(), "period": period, "interval": interval, "data": records},
            indent=2,
        )
    except Exception as e:
        return f"Error fetching history for '{ticker}': {type(e).__name__}: {e}"


@mcp.tool()
def get_stock_info(ticker: str) -> str:
    """Get company profile and descriptive information for a stock.

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
    """
    try:
        info = fetch_info(ticker)
        if not info:
            return f"No data found for ticker '{ticker}'."

        result = {
            "ticker": ticker.upper(),
            "name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "city": info.get("city"),
            "website": info.get("website"),
            "employees": info.get("fullTimeEmployees"),
            "description": info.get("longBusinessSummary"),
            "ceo": info.get("companyOfficers", [{}])[0].get("name") if info.get("companyOfficers") else None,
            "ipo_date": info.get("ipoExpectedDate"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "float_shares": info.get("floatShares"),
            "insider_ownership": info.get("heldPercentInsiders"),
            "institutional_ownership": info.get("heldPercentInstitutions"),
        }
        return json.dumps({k: v for k, v in result.items() if v is not None}, indent=2)
    except Exception as e:
        return f"Error fetching info for '{ticker}': {type(e).__name__}: {e}"
