"""
The research pipeline. Runs Serenity's five-factor bottleneck screen
end-to-end and records EVERY decision into a reasoning trace the UI renders.

Stages:
  1. universe   - load supply-chain map (themes -> segments -> tickers)
  2. crawl      - live news per segment (supply/demand signals) + per ticker
  3. market     - yfinance metrics per ticker
  4. score      - five-factor scoring with per-factor evidence
  5. select     - rank, apply conviction threshold, pick top N
  6. thesis     - write the investment thesis per pick
"""
import concurrent.futures as cf
import os
import time

from . import knowledge as kb
from . import crawler, market, thesis as thesis_mod
from . import sampledata


class Trace:
    def __init__(self):
        self.stages = []

    def stage(self, name: str, title: str, description: str):
        s = {"name": name, "title": title, "description": description,
             "started": crawler.now_iso(), "finished": None,
             "events": [], "summary": ""}
        self.stages.append(s)
        return s

    @staticmethod
    def log(stage: dict, kind: str, text: str, data=None):
        stage["events"].append({"t": crawler.now_iso(), "kind": kind,
                                "text": text, "data": data})

    @staticmethod
    def finish(stage: dict, summary: str):
        stage["finished"] = crawler.now_iso()
        stage["summary"] = summary


def run_pipeline(top_n: int = 5, progress_cb=None, demo: bool | None = None) -> dict:
    trace = Trace()
    t0 = time.time()
    if demo is None:
        demo = os.environ.get("DEMO_MODE") == "1"
    data_mode = "demo" if demo else "live"

    def prog(pct, msg):
        if progress_cb:
            progress_cb(pct, msg)

    # ---- Stage 1: universe -------------------------------------------------
    s1 = trace.stage("universe", "Map the supply chain",
                     "Load the megatrend -> segment -> company map. Serenity's rule: "
                     "start from CONFIRMED demand and reverse-engineer every input it needs.")
    companies = kb.all_companies()
    for th in kb.THEMES:
        Trace.log(s1, "theme", f"Megatrend: {th['name']} — {th['megatrend']}",
                  {"theme_id": th["id"], "demand_prior": th["demand_prior"]})
        for seg in th["segments"]:
            scoped = seg.get("in_scope", True)
            Trace.log(s1, "segment",
                      f"{seg['name']}{'' if scoped else ' [context only — too crowded to screen]'}: "
                      f"{seg['why_critical']}",
                      {"segment_id": seg["id"], "tickers": seg["tickers"],
                       "supply_prior": seg["supply_constraint_prior"],
                       "criticality": seg["criticality"], "theme_id": th["id"],
                       "in_scope": scoped})
    Trace.finish(s1, f"{len(kb.THEMES)} megatrends, "
                     f"{len(kb.scored_segments())} chokepoint segments screened "
                     f"(+context nodes), {len(companies)} US-listed candidates.")
    prog(10, "Supply chain mapped")

    # ---- Stage 2: crawl ----------------------------------------------------
    s2 = trace.stage("crawl", "Crawl live news",
                     "Google News RSS per segment keyword + per-ticker headlines. "
                     "Looking for supply-stress language (shortage, lead time, sole "
                     "supplier) and demand confirmation (capex, ramp, buildout).")
    seg_news, tick_news, crawl_ok = {}, {}, True
    segments = kb.scored_segments()
    if not demo:
        with cf.ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(crawler.crawl_segment, seg): seg["id"] for _, seg in segments}
            for fut in cf.as_completed(futs):
                sid = futs[fut]
                items = [h for h in fut.result() if "error" not in h]
                errs = [h for h in fut.result() if "error" in h]
                seg_news[sid] = items
                if errs and not items:
                    crawl_ok = False
                    Trace.log(s2, "warn", f"[{sid}] crawl failed: {errs[0]['error']}")
                else:
                    Trace.log(s2, "crawl", f"[{sid}] {len(items)} headlines",
                              {"segment_id": sid, "headlines": items[:10]})
        with cf.ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(crawler.ticker_news, c["ticker"]): c["ticker"] for c in companies}
            for fut in cf.as_completed(futs):
                tk = futs[fut]
                items = [h for h in fut.result() if "error" not in h]
                tick_news[tk] = items
    if demo or sum(len(v) for v in seg_news.values()) == 0:
        if not demo:
            data_mode = "demo-fallback"
            Trace.log(s2, "warn", "LIVE CRAWL UNAVAILABLE — falling back to bundled "
                                  "sample headlines (clearly-labeled demo data).")
        for _, seg in segments:
            seg_news[seg["id"]] = sampledata.sample_segment_news(seg["id"])
            Trace.log(s2, "crawl", f"[{seg['id']}] {len(seg_news[seg['id']])} sample headlines",
                      {"segment_id": seg["id"], "headlines": seg_news[seg["id"]]})
        for c in companies:
            tick_news[c["ticker"]] = sampledata.sample_ticker_news(c["ticker"])
    total = sum(len(v) for v in seg_news.values()) + sum(len(v) for v in tick_news.values())
    Trace.finish(s2, f"{total} headlines gathered across "
                     f"{len(seg_news)} segments and {len(tick_news)} tickers "
                     f"[{data_mode}]."
                     + ("" if crawl_ok else " (some live feeds unreachable)"))
    prog(40, "News crawled")

    # ---- Stage 3: market data ---------------------------------------------
    s3 = trace.stage("market", "Fetch market data",
                     "yfinance: price, momentum, market cap, analyst coverage, "
                     "margins, growth. Attention factors need size + coverage; "
                     "value capture needs margins + growth.")
    metrics = {}
    if not demo:
        with cf.ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(market.fetch_metrics, c["ticker"]): c["ticker"] for c in companies}
            for fut in cf.as_completed(futs):
                m = fut.result()
                metrics[m["ticker"]] = m
    ok_n = sum(1 for m in metrics.values() if m.get("ok"))
    if demo or ok_n < max(3, len(companies) // 5):
        if not demo:
            data_mode = "demo-fallback"
            Trace.log(s3, "warn", "LIVE MARKET DATA UNAVAILABLE — falling back to "
                                  "bundled sample metrics (names tagged [SAMPLE]).")
        for c in companies:
            if not metrics.get(c["ticker"], {}).get("ok"):
                metrics[c["ticker"]] = sampledata.sample_metrics(c["ticker"])
    for m in metrics.values():
        if m.get("ok"):
            Trace.log(s3, "data",
                      f"{m['ticker']} ({m['name']}): ${m.get('price') or 0:,.2f}, "
                      f"cap {('$%.2fB' % (m['market_cap']/1e9)) if m.get('market_cap') else 'n/a'}, "
                      f"{market.momentum_note(m)}", {"ticker": m["ticker"], "metrics": m})
        else:
            Trace.log(s3, "warn", f"{m['ticker']}: fetch failed ({m.get('error')})")
    ok_n = sum(1 for m in metrics.values() if m.get("ok"))
    Trace.finish(s3, f"Market data for {ok_n}/{len(companies)} tickers [{data_mode}].")
    prog(65, "Market data fetched")

    # ---- Stage 4: score ----------------------------------------------------
    s4 = trace.stage("score", "Five-factor bottleneck scoring",
                     "Serenity's model — Demand(0.15) Supply(0.25) Attention(0.25) "
                     "ValueCapture(0.20) Catalyst(0.15). Supply & attention dominate: "
                     "the alpha is the chokepoint nobody is watching yet.")
    candidates = []
    for c in companies:
        tk, seg, th = c["ticker"], c["segment"], c["theme"]
        m = metrics.get(tk, {})
        if not m.get("ok"):
            Trace.log(s4, "skip", f"{tk}: skipped (no market data)")
            continue
        snews = seg_news.get(seg["id"], [])
        tnews = tick_news.get(tk, [])

        # Factor 1: certain demand
        d_hits, d_ev = crawler.count_signal_hits(snews, kb.DEMAND_SIGNAL_WORDS)
        d_score = market.clamp(0.7 * th["demand_prior"] + 0.3 * market.clamp(d_hits / 5))
        d_evidence = [f"Theme prior {th['demand_prior']:.2f} ({th['name']})."] + \
                     [f"News: “{t}”" for t in d_ev[:2]]

        # Factor 2: constrained supply
        sup_hits, sup_ev = crawler.count_signal_hits(snews + tnews, kb.SUPPLY_SIGNAL_WORDS)
        sup_score = market.clamp(0.65 * seg["supply_constraint_prior"]
                                 + 0.35 * market.clamp(sup_hits / 4))
        sup_evidence = [f"Structural prior {seg['supply_constraint_prior']:.2f}: {seg['why_critical']}"] + \
                       [f"News: “{t}”" for t in sup_ev[:3]]

        # Factor 3: low attention
        att_score, att_evidence = market.attention_score(m, len(tnews))

        # Factor 4: value capture
        vc_score, vc_evidence = market.value_capture_score(m)

        # Factor 5: catalyst
        cat_hits, cat_ev = crawler.count_signal_hits(tnews, kb.CATALYST_SIGNAL_WORDS)
        cat_score = market.clamp(0.25 + 0.75 * market.clamp(cat_hits / 3))
        cat_evidence = [f"News: “{t}”" for t in cat_ev[:3]] or \
                       ["No explicit catalyst headline found; base 0.25."]
        if m.get("next_earnings"):
            cat_evidence.append(f"Next earnings: {m['next_earnings']}")

        factors = {
            "demand": {"score": round(d_score, 3), "evidence": d_evidence},
            "supply": {"score": round(sup_score, 3), "evidence": sup_evidence},
            "attention": {"score": round(att_score, 3), "evidence": att_evidence},
            "value_capture": {"score": round(vc_score, 3), "evidence": vc_evidence},
            "catalyst": {"score": round(cat_score, 3), "evidence": cat_evidence},
        }
        composite = sum(kb.FACTOR_WEIGHTS[k] * factors[k]["score"] for k in kb.FACTOR_WEIGHTS)
        composite *= (0.8 + 0.2 * seg["criticality"])  # criticality kicker
        cand = {
            "ticker": tk, "name": m.get("name", tk),
            "theme_id": th["id"], "theme_name": th["name"],
            "segment_id": seg["id"], "segment_name": seg["name"],
            "why_critical": seg["why_critical"],
            "factors": factors, "composite": round(composite, 4),
            "momentum_note": market.momentum_note(m),
            "metrics": {k: m.get(k) for k in
                        ("price", "market_cap", "analyst_count", "gross_margin",
                         "revenue_growth", "forward_pe", "price_to_sales",
                         "ret_1m", "ret_3m", "ret_6m", "industry", "next_earnings")},
            "headlines": tnews[:5],
        }
        candidates.append(cand)
        Trace.log(s4, "score",
                  f"{tk}: composite {composite:.3f} "
                  f"(D {d_score:.2f} / S {sup_score:.2f} / A {att_score:.2f} "
                  f"/ V {vc_score:.2f} / C {cat_score:.2f})",
                  {"candidate": cand})
    Trace.finish(s4, f"Scored {len(candidates)} candidates.")
    prog(80, "Scoring done")

    # ---- Stage 5: select ---------------------------------------------------
    s5 = trace.stage("select", "Rank & select",
                     "Rank by composite. Require supply>=0.55 AND attention>=0.35 — "
                     "a crowded or unconstrained name is not a bottleneck trade.")
    candidates.sort(key=lambda c: c["composite"], reverse=True)
    picks, rejected = [], []
    for c in candidates:
        f = c["factors"]
        if len(picks) < top_n and f["supply"]["score"] >= 0.55 and f["attention"]["score"] >= 0.35:
            picks.append(c)
            Trace.log(s5, "pick", f"#{len(picks)} {c['ticker']} — composite {c['composite']:.3f} "
                                  f"({c['segment_name']})", {"ticker": c["ticker"]})
        else:
            why = []
            if f["supply"]["score"] < 0.55:
                why.append(f"supply {f['supply']['score']:.2f} < 0.55")
            if f["attention"]["score"] < 0.35:
                why.append(f"attention {f['attention']['score']:.2f} < 0.35 (too crowded)")
            if len(picks) >= top_n and not why:
                why.append("below top-N cutoff")
            rejected.append({"ticker": c["ticker"], "composite": c["composite"],
                             "reason": "; ".join(why)})
            Trace.log(s5, "reject", f"{c['ticker']}: {'; '.join(why)}")
    Trace.finish(s5, f"{len(picks)} picks, {len(rejected)} rejected.")
    prog(88, "Picks selected")

    # ---- Stage 6: thesis ---------------------------------------------------
    s6 = trace.stage("thesis", "Write investment theses",
                     "Assemble the full argument per pick, including kill criteria. "
                     "Uses Claude API if ANTHROPIC_API_KEY is set, else template engine.")
    for p in picks:
        text, engine = thesis_mod.write_thesis(p)
        p["thesis"] = text
        p["thesis_engine"] = engine
        Trace.log(s6, "thesis", f"{p['ticker']}: thesis written ({engine})",
                  {"ticker": p["ticker"]})
    Trace.finish(s6, f"{len(picks)} theses written.")
    prog(100, "Run complete")

    return {
        "created": crawler.now_iso(),
        "data_mode": data_mode,
        "duration_sec": round(time.time() - t0, 1),
        "weights": kb.FACTOR_WEIGHTS,
        "stages": trace.stages,
        "candidates": candidates,
        "picks": picks,
        "rejected": rejected,
        "disclaimer": "Automated research tool. Not financial advice.",
    }
