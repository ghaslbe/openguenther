import yfinance as yf
from services.tool_context import get_emit_log

TOOL_DEFINITION = {
    "name": "get_stock_price",
    "description": (
        "Aktueller Aktienkurs, Kursveränderung und Kennzahlen für beliebige Aktien und Indizes weltweit. "
        "Symbol-Beispiele: 'AAPL' (Apple), 'MSFT' (Microsoft), 'NVDA' (Nvidia), "
        "'BMW.DE' (BMW), 'SAP.DE' (SAP), 'VOW3.DE' (VW), '^DAX' (DAX-Index), 'BTC-USD' (Bitcoin). "
        "Kostenlos, kein API-Key nötig (Yahoo Finance)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": (
                    "Ticker-Symbol, z.B. 'AAPL', 'BMW.DE', '^DAX', 'BTC-USD'. "
                    "Deutsche Aktien haben das Suffix '.DE', Schweizer '.SW', US-Aktien kein Suffix."
                )
            }
        },
        "required": ["symbol"]
    }
}


def get_stock_price(symbol: str) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    sym = symbol.upper().strip()
    log(f"Aktienkurs abrufen: {sym}")

    try:
        ticker = yf.Ticker(sym)
        info = ticker.info

        # Check if we got valid data
        if not info or (info.get('regularMarketPrice') is None and info.get('currentPrice') is None):
            return {"error": f"Keine Kursdaten für '{sym}' gefunden. Ticker-Symbol prüfen (z.B. 'AAPL', 'BMW.DE', '^DAX')."}

        price = info.get('currentPrice') or info.get('regularMarketPrice')
        prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
        currency = info.get('currency', '')
        name = info.get('shortName') or info.get('longName') or sym

        log(f"{name} ({sym}): {price} {currency}")

        result = {
            "symbol": sym,
            "name": name,
            "currency": currency,
            "kurs": round(price, 4) if price is not None else None,
        }

        if prev_close and price:
            change = price - prev_close
            change_pct = (change / prev_close) * 100
            result["veränderung"] = f"{change:+.2f} ({change_pct:+.2f}%)"

        for label, key in [
            ("eröffnung", "open"),
            ("tageshoch", "dayHigh"),
            ("tagestief", "dayLow"),
            ("vortageskurs", "previousClose"),
            ("52w_hoch", "fiftyTwoWeekHigh"),
            ("52w_tief", "fiftyTwoWeekLow"),
        ]:
            val = info.get(key)
            if val is not None:
                result[label] = round(val, 4)

        market_cap = info.get('marketCap')
        if market_cap:
            if market_cap >= 1e12:
                result["marktkapitalisierung"] = f"{market_cap / 1e12:.2f} Bio. {currency}"
            elif market_cap >= 1e9:
                result["marktkapitalisierung"] = f"{market_cap / 1e9:.2f} Mrd. {currency}"
            else:
                result["marktkapitalisierung"] = f"{market_cap / 1e6:.2f} Mio. {currency}"

        volume = info.get('volume') or info.get('regularMarketVolume')
        if volume:
            result["volumen"] = f"{volume:,}"

        return result

    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": f"Fehler beim Abruf von '{sym}': {str(e)}"}
