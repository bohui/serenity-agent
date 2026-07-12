"""
Supply-chain knowledge base: the agent's map of AI infrastructure and
embodied-AI value chains, decomposed into stages (value-chain layers,
top = demand, bottom = upstream inputs) and segments (nodes).

Modeled on Serenity's (@aleabitoreddit) method: start from a confirmed
megatrend, reverse-engineer the supply chain, and enumerate hard-to-replace
upstream segments that the market may not have priced in.

Segment fields:
  - stage: value-chain layer (drawn top-to-bottom in the UI map)
  - in_scope: False = context node (drawn on the map, NOT screened —
    usually too popular/large to ever be a bottleneck trade)
  - supply_constraint_prior: 0-1 structural supply tightness
    (>= BOTTLENECK_THRESHOLD renders as a highlighted bottleneck node)
  - criticality: 0-1 irreplaceability for the megatrend
  - players: notable companies [ticker, name, note] for the map node
    (may include foreign/private names; screening uses `tickers`, US-listed)
  - keywords: crawler search terms (scored segments only)
"""

BOTTLENECK_THRESHOLD = 0.75

THEMES = [
    {
        "id": "ai_infra",
        "name": "AI Infrastructure",
        "megatrend": "Hyperscaler AI datacenter capex supercycle: compute, networking, power, cooling, advanced packaging.",
        "demand_prior": 0.95,
        "segments": [
            # ---- Stage: Demand (context) ----
            {
                "id": "hyperscalers", "stage": "Demand: AI datacenters",
                "name": "Hyperscalers & AI clouds", "in_scope": False,
                "why_critical": "The confirmed megatrend: $400B+ annual AI capex funds everything below.",
                "supply_constraint_prior": 0.1, "criticality": 1.0, "keywords": [],
                "tickers": [],
                "players": [["MSFT", "Microsoft", "Azure"], ["GOOGL", "Alphabet", "GCP/TPU"],
                            ["AMZN", "Amazon", "AWS"], ["META", "Meta", ""],
                            ["ORCL", "Oracle", "OCI"]],
            },
            # ---- Stage: Compute & Networking (context) ----
            {
                "id": "accelerators", "stage": "Compute & networking",
                "name": "GPUs / AI accelerators", "in_scope": False,
                "why_critical": "The compute engine — but fully institutionalized; no attention gap.",
                "supply_constraint_prior": 0.6, "criticality": 1.0, "keywords": [],
                "tickers": [],
                "players": [["NVDA", "NVIDIA", ""], ["AMD", "AMD", ""],
                            ["AVGO", "Broadcom", "custom ASICs"]],
            },
            {
                "id": "switching", "stage": "Compute & networking",
                "name": "Switching & interconnect silicon", "in_scope": False,
                "why_critical": "Cluster scale-out fabric; well covered by the street.",
                "supply_constraint_prior": 0.4, "criticality": 0.9, "keywords": [],
                "tickers": [],
                "players": [["ANET", "Arista Networks", ""], ["MRVL", "Marvell", ""],
                            ["CRDO", "Credo", "AECs"]],
            },
            # ---- Stage: Optics & interconnect ----
            {
                "id": "optical_components", "stage": "Optics & interconnect",
                "name": "Optical transceivers, lasers & co-packaged optics",
                "why_critical": "Every GPU cluster scale-out is gated by optics; 1.6T ramp and CPO transition strain EML/VCSEL laser supply.",
                "supply_constraint_prior": 0.75, "criticality": 0.85,
                "keywords": ["optical transceiver shortage", "co-packaged optics ramp", "EML laser supply AI"],
                "tickers": ["LITE", "AAOI", "FN", "POET", "LWLG"],
                "players": [["LITE", "Lumentum", "lasers/transceivers"],
                            ["AAOI", "Applied Optoelectronics", ""],
                            ["FN", "Fabrinet", "optics manufacturing"],
                            ["POET", "POET Technologies", "optical interposer"],
                            ["LWLG", "Lightwave Logic", "EO polymers"],
                            ["COHR", "Coherent", "context: larger cap"]],
            },
            {
                "id": "inp_photonics", "stage": "Optics & interconnect",
                "name": "InP substrates & compound-semi epitaxy",
                "why_critical": "Indium phosphide substrates/epiwafers gate laser production for optical interconnects; very few merchant suppliers, years to add capacity.",
                "supply_constraint_prior": 0.95, "criticality": 0.9,
                "keywords": ["indium phosphide shortage", "InP substrate AI", "epitaxy wafer supply"],
                "tickers": ["AXTI"],
                "players": [["AXTI", "AXT Inc", "InP/GaAs substrates"],
                            ["—", "IntelliEPI", "Taiwan-listed epi foundry"],
                            ["—", "Sumitomo Electric", "Japan, integrated"],
                            ["IQE.L", "IQE plc", "UK epiwafers"]],
            },
            # ---- Stage: Packaging & materials ----
            {
                "id": "foundry_hbm", "stage": "Packaging & materials",
                "name": "Foundry & HBM memory", "in_scope": False,
                "why_critical": "CoWoS and HBM capacity gate accelerator output — but heavily covered mega-caps.",
                "supply_constraint_prior": 0.7, "criticality": 1.0, "keywords": [],
                "tickers": [],
                "players": [["TSM", "TSMC", "CoWoS"], ["MU", "Micron", "HBM"],
                            ["—", "SK hynix", "HBM leader, KRX"], ["—", "Samsung", "KRX"]],
            },
            {
                "id": "advanced_packaging", "stage": "Packaging & materials",
                "name": "Advanced packaging materials & inspection",
                "why_critical": "CoWoS/HBM stacking depends on niche materials (ABF, T-glass) and metrology; single-vendor exposure (Ajinomoto, Nitto Boseki).",
                "supply_constraint_prior": 0.8, "criticality": 0.85,
                "keywords": ["ABF substrate shortage", "T-glass supply", "HBM packaging inspection"],
                "tickers": ["CAMT", "ONTO", "UCTT", "ICHR", "AEIS"],
                "players": [["CAMT", "Camtek", "HBM inspection"],
                            ["ONTO", "Onto Innovation", "metrology"],
                            ["—", "Ajinomoto", "ABF film, sole supplier, TSE"],
                            ["—", "Nitto Boseki", "T-glass, sole supplier, TSE"]],
            },
            {
                "id": "semicap_subsystems", "stage": "Packaging & materials",
                "name": "Semicap components & fab subsystems",
                "why_critical": "Fab tool makers outsource fluid delivery, RF power, quartz; these sub-tier vendors are capacity-gated and unglamorous.",
                "supply_constraint_prior": 0.6, "criticality": 0.7,
                "keywords": ["semiconductor equipment component shortage", "fab subsystem supplier", "RF power semiconductor equipment"],
                "tickers": ["UCTT", "ICHR", "AEIS", "MKSI"],
                "players": [["UCTT", "Ultra Clean Holdings", ""],
                            ["ICHR", "Ichor Holdings", "fluid delivery"],
                            ["AEIS", "Advanced Energy", "RF power"],
                            ["MKSI", "MKS Instruments", ""]],
            },
            # ---- Stage: Power & cooling ----
            {
                "id": "power_equipment", "stage": "Power & cooling",
                "name": "Grid & datacenter power equipment",
                "why_critical": "Transformers, switchgear and power modules have multi-year lead times; interconnection queues exceed grid capacity.",
                "supply_constraint_prior": 0.85, "criticality": 0.9,
                "keywords": ["transformer lead time datacenter", "switchgear shortage AI", "datacenter power constraint"],
                "tickers": ["POWL", "VICR", "NVT", "AZZ", "BE"],
                "players": [["POWL", "Powell Industries", "switchgear"],
                            ["VICR", "Vicor", "power modules"],
                            ["NVT", "nVent Electric", ""],
                            ["AZZ", "AZZ", "galvanizing/coatings"],
                            ["BE", "Bloom Energy", "fuel cells"],
                            ["GEV", "GE Vernova", "context: crowded"],
                            ["VRT", "Vertiv", "context: crowded"]],
            },
            {
                "id": "thermal_cooling", "stage": "Power & cooling",
                "name": "Liquid cooling & thermal management",
                "why_critical": "Rack densities past 100kW force liquid cooling; specialized cold-plate/CDU capacity is scarce.",
                "supply_constraint_prior": 0.65, "criticality": 0.8,
                "keywords": ["liquid cooling datacenter shortage", "cold plate CDU supply", "immersion cooling AI"],
                "tickers": ["MOD", "SPXC", "TT"],
                "players": [["MOD", "Modine", "cooling systems"],
                            ["SPXC", "SPX Technologies", ""],
                            ["TT", "Trane Technologies", ""],
                            ["—", "Asia Vital Components", "TWSE"]],
            },
        ],
    },
    {
        "id": "embodied_ai",
        "name": "Embodied AI / Humanoid Robotics",
        "megatrend": "Humanoid & general-purpose robot production scaling from pilots to 100k+ units; the actuator stack, magnets and sensing are the physical gates.",
        "demand_prior": 0.8,
        "segments": [
            # ---- Stage: Demand (context) ----
            {
                "id": "robot_oems", "stage": "Demand: robot OEMs",
                "name": "Humanoid & robot OEMs", "in_scope": False,
                "why_critical": "The demand source: Optimus, Figure, Unitree and Chinese OEMs scaling to 100k+ units.",
                "supply_constraint_prior": 0.1, "criticality": 1.0, "keywords": [],
                "tickers": [],
                "players": [["TSLA", "Tesla", "Optimus"], ["—", "Figure AI", "private"],
                            ["—", "Unitree", "private/CN"], ["—", "Agility Robotics", "private"]],
            },
            # ---- Stage: Brain (context) ----
            {
                "id": "robot_compute", "stage": "Brain: compute & models",
                "name": "Edge AI compute & VLA models", "in_scope": False,
                "why_critical": "Robot brains — dominated by covered mega-caps; no attention gap.",
                "supply_constraint_prior": 0.3, "criticality": 0.9, "keywords": [],
                "tickers": [],
                "players": [["NVDA", "NVIDIA", "Jetson/GR00T"], ["QCOM", "Qualcomm", ""],
                            ["—", "Physical Intelligence", "private"]],
            },
            # ---- Stage: Perception ----
            {
                "id": "robot_sensing", "stage": "Perception & sensing",
                "name": "Robot perception: vision, force & torque sensing",
                "why_critical": "Every joint needs encoders/torque sensing; every robot needs low-power vision. Few merchant vendors at automotive-grade quality.",
                "supply_constraint_prior": 0.6, "criticality": 0.75,
                "keywords": ["robot vision chip demand", "force torque sensor humanoid", "lidar robotics supply"],
                "tickers": ["AMBA", "OUST", "NOVT", "TDY", "ON"],
                "players": [["AMBA", "Ambarella", "vision SoC"],
                            ["OUST", "Ouster", "lidar"],
                            ["NOVT", "Novanta", "owns ATI force/torque"],
                            ["TDY", "Teledyne", "imaging"],
                            ["ON", "onsemi", "image sensors"]],
            },
            # ---- Stage: Actuation ----
            {
                "id": "actuators_gears", "stage": "Actuation",
                "name": "Precision actuators, gears & bearings",
                "why_critical": "Harmonic/strain-wave gears are 30-50% of actuator cost with brutal precision barriers; supplier base not built for volume.",
                "supply_constraint_prior": 0.85, "criticality": 0.9,
                "keywords": ["harmonic drive shortage humanoid", "robot actuator supply chain", "precision gear robot production"],
                "tickers": ["RBC", "RRX", "TKR", "ALNT", "NOVT"],
                "players": [["—", "Harmonic Drive Systems", "TSE 6324, the namesake"],
                            ["RBC", "RBC Bearings", ""],
                            ["RRX", "Regal Rexnord", "motion control"],
                            ["TKR", "Timken", "bearings"],
                            ["ALNT", "Allient", "motion control"],
                            ["—", "Leaderdrive", "CN, SSE"]],
            },
            # ---- Stage: Materials & energy ----
            {
                "id": "rare_earth_magnets", "stage": "Materials & energy",
                "name": "Rare-earth (NdFeB) magnets ex-China",
                "why_critical": "High-torque actuators need NdFeB magnets; China controls ~90% of processing. Western mine-to-magnet capacity is the scarce asset.",
                "supply_constraint_prior": 0.9, "criticality": 0.9,
                "keywords": ["rare earth magnet supply robot", "NdFeB shortage", "rare earth export control humanoid"],
                "tickers": ["MP", "USAR", "UUUU"],
                "players": [["MP", "MP Materials", "mine-to-magnet"],
                            ["USAR", "USA Rare Earth", ""],
                            ["UUUU", "Energy Fuels", "REE separation"],
                            ["—", "Lynas", "ASX: LYC"]],
            },
            {
                "id": "robot_batteries", "stage": "Materials & energy",
                "name": "High-density batteries for mobile robots",
                "why_critical": "Humanoids need ~1-2kWh packs with high discharge rates; silicon-anode and specialty cells are supply-gated.",
                "supply_constraint_prior": 0.55, "criticality": 0.6,
                "keywords": ["silicon anode battery robot", "humanoid robot battery supplier"],
                "tickers": ["AMPX", "ENVX"],
                "players": [["AMPX", "Amprius Technologies", "silicon anode"],
                            ["ENVX", "Enovix", ""],
                            ["—", "CATL", "SZSE"]],
            },
        ],
    },
]

# Serenity's five factors and pipeline weights.
# Supply constraint and low attention carry the most weight: the edge is
# finding the chokepoint BEFORE the crowd, not confirming consensus.
FACTOR_WEIGHTS = {
    "demand": 0.15,       # certain demand from a confirmed megatrend
    "supply": 0.25,       # constrained supply, high barriers, slow replication
    "attention": 0.25,    # low market attention / not yet institutionalized
    "value_capture": 0.20, # pricing power, margins, share of value chain
    "catalyst": 0.15,     # near-term trigger for re-rating
}

# Headline keywords used as live evidence for each factor.
SUPPLY_SIGNAL_WORDS = [
    "shortage", "sole supplier", "sole-source", "lead time", "lead-time",
    "price increase", "price hike", "capacity constraint", "supply gap",
    "bottleneck", "allocation", "sold out", "backlog", "export control",
    "single source", "duopoly", "constrained",
]
DEMAND_SIGNAL_WORDS = [
    "capex", "expansion", "buildout", "record demand", "orders surge",
    "ramp", "gigawatt", "data center", "datacenter", "mass production",
    "production target", "scaling",
]
CATALYST_SIGNAL_WORDS = [
    "contract", "wins", "award", "partnership", "capacity expansion",
    "new facility", "guidance raise", "raises guidance", "breakthrough",
    "qualification", "design win", "earnings beat", "upgrade",
]


def scored_segments():
    """(theme, segment) pairs that the pipeline actually screens."""
    return [(th, seg) for th in THEMES for seg in th["segments"]
            if seg.get("in_scope", True)]


def all_companies():
    """Flatten to a list of (theme, segment, ticker) rows, deduped by ticker
    keeping the highest-criticality segment assignment."""
    rows = {}
    for theme, seg in scored_segments():
        for t in seg["tickers"]:
            if "." in t:  # skip non-US listings in v1
                continue
            prev = rows.get(t)
            if prev is None or seg["criticality"] > prev["segment"]["criticality"]:
                rows[t] = {"theme": theme, "segment": seg, "ticker": t}
    return list(rows.values())
