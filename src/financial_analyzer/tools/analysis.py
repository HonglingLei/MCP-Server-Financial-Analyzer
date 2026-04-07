"""Analytical tools: ratios, trends, comparisons, and DCF valuation."""

import json
from typing import Any

import pandas as pd

from financial_analyzer.app import mcp
from financial_analyzer.data.yahoo_finance import fetch_financials, fetch_info

_INFO_TO_FIELD: dict[str, str] = {
    "pe_ratio_ttm": "trailingPE",
    "pe_ratio_forward": "forwardPE",
    "peg_ratio": "pegRatio",
    "price_to_book": "priceToBook",
    "price_to_sales_ttm": "priceToSalesTrailing12Months",
    "ev_to_ebitda": "enterpriseToEbitda",
    "ev_to_revenue": "enterpriseToRevenue",
    "profit_margin": "profitMargins",
    "operating_margin": "operatingMargins",
    "gross_margin": "grossMargins",
    "roe": "returnOnEquity",
    "roa": "returnOnAssets",
    "debt_to_equity": "debtToEquity",
    "current_ratio": "currentRatio",
    "quick_ratio": "quickRatio",
    "revenue_growth_yoy": "revenueGrowth",
    "earnings_growth_yoy": "earningsGrowth",
    "market_cap": "marketCap",
    "current_price": "currentPrice",
    "dividend_yield": "dividendYield",
    "eps_ttm": "trailingEps",
}


def _safe(info: dict, *keys: str) -> Any:
    for k in keys:
        v = info.get(k)
        if v is not None:
            return v
    return None


@mcp.tool()
def calculate_financial_ratios(ticker: str) -> str:
    """Calculate key financial ratios for a stock.

    Returns valuation ratios (P/E, P/B, P/S, EV/EBITDA), profitability
    (ROE, ROA, profit margin, EBITDA margin), and leverage (debt/equity,
    current ratio, quick ratio).

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
    """
    try:
        info = fetch_info(ticker)
        if not info:
            return f"No data found for '{ticker}'."

        ratios: dict[str, Any] = {
            "ticker": ticker.upper(),
            "name": info.get("longName"),
            # Valuation
            "pe_ratio_ttm": _safe(info, "trailingPE"),
            "pe_ratio_forward": _safe(info, "forwardPE"),
            "peg_ratio": _safe(info, "pegRatio"),
            "price_to_book": _safe(info, "priceToBook"),
            "price_to_sales_ttm": _safe(info, "priceToSalesTrailing12Months"),
            "ev_to_ebitda": _safe(info, "enterpriseToEbitda"),
            "ev_to_revenue": _safe(info, "enterpriseToRevenue"),
            # Profitability
            "profit_margin": _safe(info, "profitMargins"),
            "operating_margin": _safe(info, "operatingMargins"),
            "ebitda_margin": _safe(info, "ebitdaMargins"),
            "gross_margin": _safe(info, "grossMargins"),
            "roe": _safe(info, "returnOnEquity"),
            "roa": _safe(info, "returnOnAssets"),
            # Leverage & liquidity
            "debt_to_equity": _safe(info, "debtToEquity"),
            "current_ratio": _safe(info, "currentRatio"),
            "quick_ratio": _safe(info, "quickRatio"),
            # Per-share
            "eps_ttm": _safe(info, "trailingEps"),
            "eps_forward": _safe(info, "forwardEps"),
            "book_value_per_share": _safe(info, "bookValue"),
            "dividend_yield": _safe(info, "dividendYield"),
            "payout_ratio": _safe(info, "payoutRatio"),
            # Growth
            "revenue_growth_yoy": _safe(info, "revenueGrowth"),
            "earnings_growth_yoy": _safe(info, "earningsGrowth"),
        }

        return json.dumps({k: v for k, v in ratios.items() if v is not None}, indent=2)
    except Exception as e:
        return f"Error calculating ratios for '{ticker}': {type(e).__name__}: {e}"


@mcp.tool()
def analyze_trends(ticker: str, metric: str = "revenue", periods: int = 4) -> str:
    """Analyse YoY / period-over-period growth trends for a financial metric.

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
        metric: Line item to analyse. Common values:
                'Total Revenue', 'Gross Profit', 'Net Income',
                'Operating Income', 'EBITDA', 'Free Cash Flow',
                'Total Assets', 'Total Debt'
        periods: Number of annual periods to include (1-8)
    """
    try:
        periods = max(1, min(8, periods))
        data = fetch_financials(ticker, keys=["income_stmt_annual", "balance_sheet_annual", "cash_flow_annual"])

        # Try income statement first, then balance sheet, then cash flow
        for key in ("income_stmt_annual", "balance_sheet_annual", "cash_flow_annual"):
            df: pd.DataFrame | None = data.get(key)
            if df is not None and not df.empty:
                # Case-insensitive match on row index
                matches = [idx for idx in df.index if metric.lower() in str(idx).lower()]
                if matches:
                    row = df.loc[matches[0]].dropna()
                    row = row.iloc[:periods]
                    values = []
                    for date, val in row.items():
                        date_str = date.isoformat() if isinstance(date, pd.Timestamp) else str(date)
                        v = val.item() if hasattr(val, "item") else float(val)
                        values.append({"date": date_str, "value": v})

                    # Calculate period-over-period growth
                    for i in range(1, len(values)):
                        prev = values[i]["value"]
                        curr = values[i - 1]["value"]
                        if prev and prev != 0:
                            values[i - 1]["growth_vs_prior"] = round((curr - prev) / abs(prev), 4)

                    return json.dumps(
                        {
                            "ticker": ticker.upper(),
                            "metric": str(matches[0]),
                            "periods": values,
                        },
                        indent=2,
                    )

        return (
            f"Metric '{metric}' not found for '{ticker}'. "
            f"Try exact names like 'Total Revenue', 'Net Income', 'Gross Profit'."
        )
    except Exception as e:
        return f"Error analysing trends for '{ticker}': {type(e).__name__}: {e}"


@mcp.tool()
def compare_stocks(tickers: list[str], metric: str = "pe_ratio_ttm") -> str:
    """Compare multiple stocks side-by-side on a single metric.

    Args:
        tickers: List of ticker symbols, e.g. ['AAPL', 'MSFT', 'GOOGL']
        metric: Metric to compare. Options include:
                'pe_ratio_ttm', 'pe_ratio_forward', 'price_to_book',
                'price_to_sales_ttm', 'ev_to_ebitda', 'profit_margin',
                'roe', 'roa', 'debt_to_equity', 'current_ratio',
                'revenue_growth_yoy', 'earnings_growth_yoy',
                'market_cap', 'current_price', 'dividend_yield'
    """
    try:
        yf_field = _INFO_TO_FIELD.get(metric, metric)
        comparison: list[dict] = []
        errors: list[str] = []

        for t in tickers[:10]:  # cap at 10
            try:
                info = fetch_info(t)
                val = info.get(yf_field) or info.get(metric)
                comparison.append(
                    {
                        "ticker": t.upper(),
                        "name": info.get("longName") or info.get("shortName"),
                        metric: val,
                    }
                )
            except Exception as e:
                errors.append(f"{t}: {e}")

        # Sort by metric value descending where possible
        comparison.sort(
            key=lambda x: (x[metric] is not None, x[metric] or 0),
            reverse=True,
        )

        result: dict[str, Any] = {"metric": metric, "comparison": comparison}
        if errors:
            result["errors"] = errors
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error comparing stocks: {type(e).__name__}: {e}"


@mcp.tool()
def dcf_estimate(
    ticker: str,
    growth_rate: float = 0.10,
    discount_rate: float = 0.10,
    terminal_growth_rate: float = 0.03,
    projection_years: int = 5,
) -> str:
    """Estimate intrinsic value using a simplified Discounted Cash Flow (DCF) model.

    Uses trailing free cash flow from Yahoo Finance as the base, projects it
    forward, and discounts back to present value.

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'
        growth_rate: Annual FCF growth rate for the projection period (e.g. 0.10 = 10%)
        discount_rate: Weighted average cost of capital / required return (e.g. 0.10 = 10%)
        terminal_growth_rate: Perpetual growth rate after projection period (e.g. 0.03 = 3%)
        projection_years: Number of years to project (1-10)
    """
    try:
        projection_years = max(1, min(10, projection_years))
        info = fetch_info(ticker)
        if not info:
            return f"No data found for '{ticker}'."

        base_fcf = info.get("freeCashflow")
        shares = info.get("sharesOutstanding")
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")

        if not base_fcf:
            return (
                f"Free cash flow data not available for '{ticker}' via Yahoo Finance. "
                f"This model requires trailing FCF."
            )
        if not shares:
            return f"Shares outstanding not available for '{ticker}'."

        # Project FCF and discount to PV
        projected: list[dict] = []
        pv_sum = 0.0
        fcf = float(base_fcf)

        for year in range(1, projection_years + 1):
            fcf *= 1 + growth_rate
            pv = fcf / ((1 + discount_rate) ** year)
            pv_sum += pv
            projected.append(
                {
                    "year": year,
                    "projected_fcf": round(fcf),
                    "present_value": round(pv),
                }
            )

        # Terminal value (Gordon Growth Model)
        terminal_fcf = fcf * (1 + terminal_growth_rate)
        if discount_rate <= terminal_growth_rate:
            return "Error: discount_rate must be greater than terminal_growth_rate."
        terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)
        pv_terminal = terminal_value / ((1 + discount_rate) ** projection_years)

        intrinsic_value = pv_sum + pv_terminal
        intrinsic_per_share = intrinsic_value / shares
        margin_of_safety = None
        if current_price:
            margin_of_safety = round((intrinsic_per_share - current_price) / current_price, 4)

        result = {
            "ticker": ticker.upper(),
            "name": info.get("longName"),
            "assumptions": {
                "base_fcf": base_fcf,
                "growth_rate": growth_rate,
                "discount_rate": discount_rate,
                "terminal_growth_rate": terminal_growth_rate,
                "projection_years": projection_years,
            },
            "projected_cash_flows": projected,
            "terminal_value": round(terminal_value),
            "pv_terminal_value": round(pv_terminal),
            "total_pv_fcf": round(pv_sum),
            "total_intrinsic_value": round(intrinsic_value),
            "shares_outstanding": shares,
            "intrinsic_value_per_share": round(intrinsic_per_share, 2),
            "current_price": current_price,
            "margin_of_safety": margin_of_safety,
            "note": (
                "This is a simplified DCF model for educational purposes. "
                "Assumptions significantly affect the output. Not financial advice."
            ),
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error running DCF for '{ticker}': {type(e).__name__}: {e}"
