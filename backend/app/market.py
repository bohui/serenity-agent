"""
Market data via yfinance (free, ~15-min delayed): price, momentum,
size/attention proxies, and value-capture fundamentals.
"""
import math


def fetch_metrics(ticker: str) -> dict:
    """Return a metrics dict; 'ok': False with 'error' if fetch failed."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.info or {}
        hist = t.history(period="6mo", interval="1d", auto_adjust=True)

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        m = {
            "ok": True,
            "ticker": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "price": price,
            "market_cap": info.get("marketCap"),
            "analyst_count": info.get("numberOfAnalystOpinions"),
            "gross_margin": info.get("grossMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "forward_pe": info.get("forwardPE"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "short_pct_float": info.get("shortPercentOfFloat"),
            "avg_volume": info.get("averageVolume"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "next_earnings": None,
            "ret_1m": None, "ret_3m": None, "ret_6m": None,
        }
        try:
            cal = t.calendar
            dates = (cal or {}).get("Earnings Date") if isinstance(cal, dict) else None
            if dates:
                m["next_earnings"] = str(dates[0])
        except Exception:
            pass
        if hist is not None and len(hist) > 22:
            close = hist["Close"]
            last = float(close.iloc[-1])
            if price is None:
                m["price"] = last

            def ret(days):
                if len(close) > days:
                    base = float(close.iloc[-days - 1])
                    return (last / base - 1.0) if base else None
                base = float(close.iloc[0])
                return (last / base - 1.0) if base else None

            m["ret_1m"], m["ret_3m"], m["ret_6m"] = ret(21), ret(63), ret(126)
        return m
    except Exception as e:
        return {"ok": False, "ticker": ticker, "error": f"{type(e).__name__}: {e}"}


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def attention_score(m: dict, mention_count: int) -> tuple[float, list[str]]:
    """Low attention = high score. Small cap, thin analyst coverage, few
    media mentions => the market hasn't arrived yet."""
    ev = []
    cap = m.get("market_cap")
    if cap:
        # <$500M: ~1.0 ... >$50B: ~0.0 (log scale)
        s_cap = clamp(1.0 - (math.log10(cap) - 8.7) / 2.0)
        ev.append(f"Market cap ${cap/1e9:.2f}B -> obscurity {s_cap:.2f}")
    else:
        s_cap, _ = 0.5, ev.append("Market cap unknown -> neutral 0.50")
    ac = m.get("analyst_count")
    if ac is not None:
        s_an = clamp(1.0 - ac / 20.0)
        ev.append(f"{ac} analysts covering -> coverage-gap {s_an:.2f}")
    else:
        s_an = 0.7
        ev.append("No analyst count found -> likely under-covered 0.70")
    s_news = clamp(1.0 - mention_count / 12.0)
    ev.append(f"{mention_count} recent media mentions -> media-quiet {s_news:.2f}")

    # Penalize names that already ran (institutional rotation likely arrived)
    r6 = m.get("ret_6m")
    penalty = 0.0
    if r6 is not None and r6 > 1.0:
        penalty = clamp((r6 - 1.0) * 0.3, 0, 0.3)
        ev.append(f"6-mo return {r6*100:.0f}% -> 'already discovered' penalty -{penalty:.2f}")
    score = clamp(0.45 * s_cap + 0.3 * s_an + 0.25 * s_news - penalty)
    return score, ev


def value_capture_score(m: dict) -> tuple[float, list[str]]:
    ev = []
    gm = m.get("gross_margin")
    if gm is not None:
        s_gm = clamp(gm / 0.6)
        ev.append(f"Gross margin {gm*100:.0f}% -> pricing power {s_gm:.2f}")
    else:
        s_gm = 0.4
        ev.append("Gross margin unknown -> 0.40")
    rg = m.get("revenue_growth")
    if rg is not None:
        s_rg = clamp(0.5 + rg)
        ev.append(f"Revenue growth {rg*100:.0f}% YoY -> demand flow-through {s_rg:.2f}")
    else:
        s_rg = 0.4
        ev.append("Revenue growth unknown -> 0.40")
    return clamp(0.55 * s_gm + 0.45 * s_rg), ev


def momentum_note(m: dict) -> str:
    parts = []
    for k, label in [("ret_1m", "1M"), ("ret_3m", "3M"), ("ret_6m", "6M")]:
        v = m.get(k)
        if v is not None:
            parts.append(f"{label} {v*100:+.0f}%")
    return ", ".join(parts) or "no price history"
