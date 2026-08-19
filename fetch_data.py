import json
import sys
from datetime import datetime, timezone, timedelta

import yfinance as yf

TICKERS = [
    {"name": "SK하이닉스", "code": "000660", "yf": "000660.KS"},
    {"name": "삼성전자", "code": "005930", "yf": "005930.KS"},
    {"name": "삼성SDI", "code": "006400", "yf": "006400.KS"},
    {"name": "TIGER 코리아AI전력기기TOP3플러스", "code": "0117V0", "yf": "0117V0.KS"},
    {"name": "현대로템", "code": "064350", "yf": "064350.KS"},
    {"name": "TIGER 미국S&P500선물(H)", "code": "143850", "yf": "143850.KS"},
    {"name": "PLUS 고배당주", "code": "161510", "yf": "161510.KS"},
    {"name": "레인보우로보틱스", "code": "277810", "yf": "277810.KQ"},
    {"name": "알지노믹스", "code": "476830", "yf": "476830.KQ"},
    {"name": "코아시아", "code": "045970", "yf": "045970.KQ"},
    {"name": "LG전자", "code": "066570", "yf": "066570.KS"},
    {"name": "에이엘티", "code": "172670", "yf": "172670.KQ"},
    {"name": "KODEX 200", "code": "069500", "yf": "069500.KS"},
    {"name": "TIGER 미국나스닥100", "code": "133690", "yf": "133690.KS"},
    {"name": "KIWOOM 국고채10년", "code": "148070", "yf": "148070.KS"},
    {"name": "TIGER 미국S&P500", "code": "360750", "yf": "360750.KS"},
    {"name": "TIGER 미국배당다우존스", "code": "458730", "yf": "458730.KS"},
    {"name": "코카콜라", "code": "KO", "yf": "KO"},
    {"name": "애플", "code": "AAPL", "yf": "AAPL"},
    {"name": "리비안 오토모티브", "code": "RIVN", "yf": "RIVN"},
    {"name": "SCHWAB US DIVIDEND EQUITY", "code": "SCHD", "yf": "SCHD"},
    {"name": "버크셔 해서웨이 B", "code": "BRK.B", "yf": "BRK-B"},
    {"name": "VOLATILITY SHARES BITCOIN STRATEGY 2X", "code": "BITX", "yf": "BITX"},
]

KST = timezone(timedelta(hours=9))


def fetch_one(entry):
    yf_ticker = entry["yf"]
    try:
        hist = yf.Ticker(yf_ticker).history(period="2mo", auto_adjust=False)
        if hist.empty or len(hist) < 2:
            return {**entry, "error": "no data returned"}

        closes = hist["Close"].dropna()
        last_close = float(closes.iloc[-1])
        prev_close = float(closes.iloc[-2])
        change_pct = round((last_close - prev_close) / prev_close * 100, 2)

        ma20_window = closes.tail(20)
        ma20 = round(float(ma20_window.mean()), 2) if len(ma20_window) >= 5 else None
        trend = None
        gap_pct = None
        if ma20:
            gap_pct = round((last_close - ma20) / ma20 * 100, 2)
            trend = "above" if last_close >= ma20 else "below"

        last_date = closes.index[-1]
        volume = hist["Volume"].dropna()
        last_volume = int(volume.iloc[-1]) if len(volume) else None

        return {
            **entry,
            "asOfDate": last_date.strftime("%Y-%m-%d"),
            "close": round(last_close, 2),
            "prevClose": round(prev_close, 2),
            "changePct": change_pct,
            "ma20": ma20,
            "ma20DataPoints": len(ma20_window),
            "ma20GapPct": gap_pct,
            "trendVsMa20": trend,
            "volume": last_volume,
        }
    except Exception as exc:
        return {**entry, "error": str(exc)}


def main():
    results = [fetch_one(t) for t in TICKERS]
    failed = [r["name"] for r in results if "error" in r]
    if failed:
        print(f"WARN: failed to fetch: {failed}", file=sys.stderr)

    payload = {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "generatedAtKst": datetime.now(KST).isoformat(),
        "source": "yfinance",
        "stocks": results,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote data.json with {len(results)} stocks ({len(failed)} failed)")


if __name__ == "__main__":
    main()
