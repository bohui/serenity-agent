"""
Bundled sample data for offline/demo mode. Used ONLY when live feeds are
unreachable (or DEMO_MODE=1); every use is flagged in the reasoning trace.
Values are plausible placeholders, NOT live market data.
"""

# ticker: (name, price, cap_$B, analysts, gross_margin, rev_growth, r1m, r3m, r6m, industry)
_ROWS = {
    "AXTI": ("AXT Inc", 8.90, 0.39, 3, 0.28, 0.34, 0.12, 0.45, 0.90, "Semiconductors"),
    "AAOI": ("Applied Optoelectronics", 22.10, 1.10, 5, 0.26, 0.42, 0.08, 0.22, 0.60, "Optical Components"),
    "LITE": ("Lumentum", 95.00, 6.60, 14, 0.35, 0.21, 0.05, 0.18, 0.55, "Optical Components"),
    "FN":   ("Fabrinet", 260.0, 9.40, 9, 0.13, 0.19, 0.03, 0.12, 0.30, "EMS / Optics"),
    "POET": ("POET Technologies", 4.60, 0.32, 2, 0.10, 0.80, 0.15, 0.35, 1.10, "Photonics"),
    "LWLG": ("Lightwave Logic", 3.10, 0.38, 1, 0.05, 0.50, -0.05, 0.10, 0.25, "EO Materials"),
    "POWL": ("Powell Industries", 240.0, 2.90, 6, 0.27, 0.15, 0.06, 0.20, 0.45, "Electrical Equipment"),
    "VICR": ("Vicor", 48.00, 2.10, 4, 0.51, 0.12, 0.04, 0.15, 0.28, "Power Modules"),
    "NVT":  ("nVent Electric", 78.00, 12.8, 15, 0.40, 0.11, 0.02, 0.10, 0.22, "Electrical Equipment"),
    "AZZ":  ("AZZ Inc", 98.00, 2.90, 5, 0.24, 0.06, 0.03, 0.08, 0.18, "Industrial Coatings"),
    "BE":   ("Bloom Energy", 28.00, 6.40, 18, 0.25, 0.18, 0.10, 0.30, 0.85, "Fuel Cells"),
    "MOD":  ("Modine Manufacturing", 130.0, 6.80, 8, 0.25, 0.09, 0.05, 0.16, 0.40, "Thermal Management"),
    "SPXC": ("SPX Technologies", 175.0, 8.10, 8, 0.30, 0.13, 0.02, 0.09, 0.25, "HVAC / Cooling"),
    "TT":   ("Trane Technologies", 420.0, 94.0, 22, 0.35, 0.11, 0.01, 0.06, 0.12, "HVAC"),
    "CAMT": ("Camtek", 92.00, 4.30, 7, 0.50, 0.30, 0.07, 0.20, 0.50, "Semi Inspection"),
    "ONTO": ("Onto Innovation", 180.0, 8.90, 10, 0.54, 0.24, 0.04, 0.14, 0.30, "Semi Metrology"),
    "UCTT": ("Ultra Clean Holdings", 42.00, 1.90, 6, 0.17, 0.16, 0.06, 0.18, 0.35, "Semicap Subsystems"),
    "ICHR": ("Ichor Holdings", 33.00, 1.10, 6, 0.13, 0.14, 0.05, 0.15, 0.30, "Fluid Delivery"),
    "AEIS": ("Advanced Energy", 130.0, 4.90, 9, 0.36, 0.12, 0.03, 0.10, 0.20, "RF Power"),
    "MKSI": ("MKS Instruments", 125.0, 8.40, 11, 0.47, 0.08, 0.02, 0.07, 0.15, "Semicap Components"),
    "MP":   ("MP Materials", 62.00, 10.2, 12, 0.30, 0.25, 0.08, 0.28, 0.75, "Rare Earths"),
    "USAR": ("USA Rare Earth", 14.00, 1.30, 3, 0.10, 0.60, 0.12, 0.40, 1.20, "Rare Earth Magnets"),
    "UUUU": ("Energy Fuels", 9.50, 1.90, 5, 0.22, 0.30, 0.06, 0.20, 0.55, "Uranium / Rare Earths"),
    "RBC":  ("RBC Bearings", 330.0, 10.4, 9, 0.44, 0.07, 0.02, 0.08, 0.16, "Precision Bearings"),
    "RRX":  ("Regal Rexnord", 160.0, 10.6, 10, 0.37, 0.03, 0.01, 0.05, 0.10, "Motion Control"),
    "TKR":  ("Timken", 92.00, 6.40, 11, 0.31, 0.02, 0.01, 0.04, 0.08, "Bearings"),
    "ALNT": ("Allient Inc", 38.00, 0.64, 3, 0.32, 0.08, 0.05, 0.14, 0.30, "Motion Control"),
    "NOVT": ("Novanta", 150.0, 5.40, 8, 0.46, 0.09, 0.02, 0.07, 0.14, "Precision Motion / Photonics"),
    "AMBA": ("Ambarella", 78.00, 3.30, 12, 0.62, 0.22, 0.06, 0.18, 0.42, "Vision SoC"),
    "OUST": ("Ouster", 12.00, 0.62, 4, 0.38, 0.35, 0.10, 0.25, 0.60, "Lidar"),
    "TDY":  ("Teledyne", 520.0, 24.5, 12, 0.43, 0.06, 0.01, 0.05, 0.10, "Sensors / Imaging"),
    "ON":   ("onsemi", 62.00, 26.0, 28, 0.45, 0.02, 0.02, 0.06, 0.10, "Power Semis"),
    "AMPX": ("Amprius Technologies", 9.00, 1.10, 4, 0.15, 0.90, 0.15, 0.45, 1.30, "Silicon-Anode Batteries"),
    "ENVX": ("Enovix", 11.00, 2.20, 8, 0.12, 0.70, 0.08, 0.20, 0.50, "Batteries"),
}

SAMPLE_SEGMENT_NEWS = {
    "inp_photonics": [
        "IntelliEPI CEO: InP shortage is a bottleneck for the entire AI infrastructure",
        "Indium phosphide substrate lead times stretch as photonics demand ramps",
        "AI datacenter buildout drives record compound-semi epiwafer orders",
    ],
    "optical_components": [
        "1.6T optical transceiver ramp constrained by EML laser supply",
        "Co-packaged optics enters next-gen AI switch platforms",
        "Hyperscaler capex guidance lifts optical component orders backlog",
    ],
    "power_equipment": [
        "Transformer lead times exceed three years as datacenter demand surges",
        "Grid interconnection queue now exceeds total installed US capacity",
        "Switchgear makers sold out through 2027 on AI datacenter buildout",
    ],
    "thermal_cooling": [
        "Liquid cooling capacity constrained as rack density passes 120kW",
        "Cold plate and CDU suppliers report record backlog on AI ramp",
    ],
    "advanced_packaging": [
        "Ajinomoto raises ABF prices 30%, projects supply gap into 2027",
        "T-glass sole supplier Nitto Boseki hikes prices; no new capacity until late 2026",
        "HBM packaging inspection demand accelerates with 12-layer stacking",
    ],
    "semicap_subsystems": [
        "Fab subsystem suppliers see allocation as tool makers ramp capacity",
    ],
    "rare_earth_magnets": [
        "China tightens rare earth export controls; NdFeB magnet supply gap widens",
        "MIIT targets 100,000 humanoid robots in 2026, straining magnet supply chain",
        "Western mine-to-magnet capacity years behind projected robot demand",
    ],
    "actuators_gears": [
        "Harmonic drive capacity sold out as humanoid programs enter mass production",
        "Actuator stack emerges as the true bottleneck in humanoid scaling",
        "Precision gear suppliers report multi-year backlog from robotics orders",
    ],
    "robot_sensing": [
        "Robot vision chip demand accelerates with humanoid pilot deployments",
        "Force-torque sensor supply constrained at automotive-grade quality",
    ],
    "robot_batteries": [
        "Silicon-anode battery makers land humanoid robot design wins",
    ],
}

SAMPLE_TICKER_NEWS = {
    "AXTI": ["AXT wins multi-year InP substrate contract with photonics leader",
             "AXT expands indium phosphide capacity on AI interconnect demand"],
    "POWL": ["Powell Industries wins record datacenter switchgear award",
             "Powell raises guidance on electrical infrastructure backlog"],
    "MP":   ["MP Materials signs magnet supply partnership for robotics",
             "MP Materials commissions new NdFeB magnet facility"],
    "ALNT": ["Allient wins humanoid actuator motor design win"],
    "USAR": ["USA Rare Earth begins magnet qualification with robotics OEM"],
    "AMPX": ["Amprius lands humanoid robot battery contract"],
    "UCTT": ["Ultra Clean wins new fab subsystem qualification"],
    "CAMT": ["Camtek receives record HBM inspection orders"],
    "VICR": ["Vicor power module qualification win for AI accelerator boards"],
    "MOD":  ["Modine expands datacenter cooling capacity with new facility"],
}


def sample_metrics(ticker: str) -> dict:
    row = _ROWS.get(ticker)
    if not row:
        return {"ok": False, "ticker": ticker, "error": "no sample data"}
    name, price, cap, an, gm, rg, r1, r3, r6, ind = row
    return {
        "ok": True, "ticker": ticker, "name": name + " [SAMPLE]",
        "price": price, "market_cap": cap * 1e9, "analyst_count": an,
        "gross_margin": gm, "revenue_growth": rg,
        "forward_pe": None, "price_to_sales": None, "short_pct_float": None,
        "avg_volume": None, "sector": None, "industry": ind,
        "next_earnings": None, "ret_1m": r1, "ret_3m": r3, "ret_6m": r6,
    }


def sample_segment_news(segment_id: str) -> list[dict]:
    return [{"title": t, "url": "", "published": "", "source": "sample",
             "query": segment_id} for t in SAMPLE_SEGMENT_NEWS.get(segment_id, [])]


def sample_ticker_news(ticker: str) -> list[dict]:
    return [{"title": t, "url": "", "published": "", "source": "sample",
             "query": ticker} for t in SAMPLE_TICKER_NEWS.get(ticker, [])]
