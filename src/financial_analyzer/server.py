import os

from dotenv import load_dotenv

load_dotenv()

from financial_analyzer.app import mcp  # noqa: E402

# Import tool/resource modules so their @mcp.tool() / @mcp.resource() decorators fire
from financial_analyzer.tools import stock_prices  # noqa: F401, E402
from financial_analyzer.tools import fundamentals  # noqa: F401, E402
from financial_analyzer.tools import sec_filings  # noqa: F401, E402
from financial_analyzer.tools import analysis  # noqa: F401, E402
from financial_analyzer.resources import market_overview  # noqa: F401, E402


def main() -> None:
    transport = os.getenv("TRANSPORT", "stdio")

    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        import uvicorn
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        mcp.settings.transport_security = None  # disable localhost-only DNS rebinding check
        uvicorn.run(mcp.streamable_http_app(), host=host, port=port)


if __name__ == "__main__":
    main()
