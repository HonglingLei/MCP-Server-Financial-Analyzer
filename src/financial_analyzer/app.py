from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Financial Analyzer",
    instructions=(
        "A financial analysis server providing stock prices, fundamentals, "
        "SEC filings (10-K/10-Q), and analytical tools. "
        "Use get_stock_price for current quotes, get_income_statement / "
        "get_balance_sheet / get_cash_flow for fundamentals, "
        "search_sec_filings / get_filing_sections for SEC documents, and "
        "calculate_financial_ratios / compare_stocks / dcf_estimate for analysis."
    ),
)
