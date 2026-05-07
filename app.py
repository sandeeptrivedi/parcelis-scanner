import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import csv
import io
import time
from urllib.parse import urlparse
from datetime import datetime

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Parcelis Outreach Scanner",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main { background: #f8f9fa; }

.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1100px; }

/* Header */
.parcelis-header {
    background: #0056D2;
    color: white;
    padding: 1.25rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.parcelis-header h1 { font-size: 1.3rem; font-weight: 600; margin: 0; color: white; }
.parcelis-header p { font-size: 0.8rem; margin: 0; opacity: 0.8; }
.header-badge {
    background: rgba(255,255,255,0.2);
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    color: white;
}

/* Pipeline steps */
.pipeline-bar {
    display: flex;
    align-items: center;
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 10px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    gap: 0;
}
.pipe-step {
    flex: 1;
    text-align: center;
    position: relative;
}
.pipe-step:not(:last-child)::after {
    content: '';
    position: absolute;
    top: 18px;
    right: 0;
    width: 100%;
    height: 1px;
    background: #dee2e6;
    z-index: 0;
    left: 50%;
}
.pipe-num {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 0 auto 6px;
    position: relative;
    z-index: 1;
    border: 2px solid #dee2e6;
    background: white;
    color: #6c757d;
}
.pipe-num.active { background: #0056D2; border-color: #0056D2; color: white; }
.pipe-num.done { background: #28a745; border-color: #28a745; color: white; }
.pipe-label { font-size: 0.72rem; color: #6c757d; line-height: 1.3; }
.pipe-label strong { display: block; color: #1a2b4a; font-size: 0.78rem; }

/* Result cards */
.result-card {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.result-card h3 { font-size: 1rem; font-weight: 600; color: #1a2b4a; margin-bottom: 0.25rem; }

/* Metric boxes */
.metric-box {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 0.85rem 1rem;
    text-align: center;
}
.metric-box .label { font-size: 0.7rem; color: #6c757d; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }
.metric-box .value { font-size: 1.1rem; font-weight: 600; color: #1a2b4a; margin-top: 4px; }
.metric-box .value.small { font-size: 0.85rem; }

/* Copy blocks */
.copy-block {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    font-size: 0.875rem;
    line-height: 1.65;
    color: #1a2b4a;
    white-space: pre-wrap;
    font-family: 'Inter', sans-serif;
}
.copy-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #6c757d;
    margin-bottom: 0.5rem;
}

/* Badges */
.badge-detected {
    display: inline-block;
    background: #fff3cd;
    color: #856404;
    border: 1px solid #ffc107;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    margin: 2px;
}
.badge-clear {
    display: inline-block;
    background: #d1e7dd;
    color: #0f5132;
    border: 1px solid #28a745;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
}
.badge-platform {
    display: inline-block;
    background: #cfe2ff;
    color: #084298;
    border: 1px solid #0056D2;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
}

/* Contact card */
.contact-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 0.9rem;
    margin-bottom: 0.75rem;
}
.contact-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #cfe2ff;
    color: #084298;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.8rem;
    flex-shrink: 0;
}
.contact-name { font-weight: 600; font-size: 0.9rem; color: #1a2b4a; }
.contact-title { font-size: 0.8rem; color: #6c757d; }
.contact-reason { font-size: 0.8rem; color: #495057; margin-top: 6px; line-height: 1.5; }

/* Suggest row */
.suggest-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    background: white;
}
.suggest-title { font-weight: 600; font-size: 0.875rem; color: #1a2b4a; }
.suggest-why { font-size: 0.8rem; color: #6c757d; margin-top: 2px; }
.suggest-search { font-size: 0.75rem; color: #0056D2; margin-top: 4px; }

/* Sidebar */
.sidebar-brand {
    background: #0056D2;
    color: white;
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    text-align: center;
}
.sidebar-brand h2 { color: white; font-size: 1rem; margin: 0; }
.sidebar-brand p { color: rgba(255,255,255,0.75); font-size: 0.75rem; margin: 4px 0 0; }

div[data-testid="stForm"] { border: none; padding: 0; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  SCANNER ENGINE  (same logic as parcelis_scanner.py)
# ════════════════════════════════════════════════════════════════

PROTECTION_APPS = {
    "Route": {
        "domains": ["route.com", "routeapp.io", "cdn.routeapp.io"],
        "keywords": ["route-widget", "route_order_protection", "RouteApp", "route-insurance", "addRouteProtection"],
    },
    "Navidium": {
        "domains": ["navidium.com", "navidiumshipping.com", "cdn.navidium.com"],
        "keywords": ["navidium", "navidium-protection", "NavidiumWidget"],
    },
    "ShipInsure": {
        "domains": ["shipinsure.com"],
        "keywords": ["shipinsure", "ShipInsure"],
    },
    "Corso": {
        "domains": ["corso.com", "corso-platform.com"],
        "keywords": ["corso-protection", "CorsoProtection", "corso_widget"],
    },
    "Redo": {
        "domains": ["getredo.com", "redo.com"],
        "keywords": ["redo-protection", "ReDoProtection", "redo_coverage"],
    },
    "AfterShip Protection": {
        "domains": ["aftership.com"],
        "keywords": ["aftership-protection", "AfterShipProtection", "as-protection"],
    },
    "Seel": {
        "domains": ["seel.com"],
        "keywords": ["seel-protection", "SeelProtection", "seel_widget"],
    },
    "Cover Genius": {
        "domains": ["covergenius.com", "xcover.com"],
        "keywords": ["covergenius", "CoverGenius", "xcover"],
    },
    "Extend": {
        "domains": ["helloextend.com", "extend.com"],
        "keywords": ["helloextend", "Extend-Protection", "ExtendProtection"],
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

TITLE_PRIORITY = {
    "founder": 1, "co-founder": 1, "ceo": 1, "coo": 2,
    "head of ecommerce": 2, "head of operations": 2, "head of growth": 2,
    "vp": 3, "director": 4, "manager": 5,
}


def scan_protection_apps(url: str) -> dict:
    result = {"found": [], "confidence": "none", "signals": [], "pages_scanned": [], "error": None}
    pages = [url, url.rstrip("/") + "/cart"]
    all_html = ""
    for page in pages:
        try:
            r = requests.get(page, headers=HEADERS, timeout=12, allow_redirects=True)
            if r.status_code == 200:
                all_html += r.text
                result["pages_scanned"].append(page)
        except Exception as e:
            result["signals"].append(f"Fetch error: {str(e)[:60]}")
    if not all_html:
        result["error"] = "Could not fetch site content"
        return result
    html_lower = all_html.lower()
    for app_name, app_data in PROTECTION_APPS.items():
        hits = []
        for domain in app_data["domains"]:
            if domain.lower() in html_lower:
                hits.append(f"domain: {domain}")
        for kw in app_data["keywords"]:
            if kw.lower() in html_lower:
                hits.append(f"keyword: {kw}")
        if hits:
            result["found"].append({"app": app_name, "signals": hits, "count": len(hits)})
    if result["found"]:
        result["confidence"] = "high" if max(a["count"] for a in result["found"]) >= 2 else "medium"
    return result


def estimate_metrics(url: str, brand_name: str) -> dict:
    result = {
        "platform": "Unknown", "price_range": {}, "aov_estimate": None,
        "aov_confidence": "low", "volume_tier": None,
        "annual_order_estimate": None, "revenue_tier": None, "signals": [],
    }
    try:
        r = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
        html = r.text
        soup = BeautifulSoup(html, "lxml")
    except Exception as e:
        result["signals"].append(f"Fetch error: {str(e)[:60]}")
        return result

    if "cdn.shopify.com" in html or "myshopify.com" in html:
        result["platform"] = "Shopify"
    elif "woocommerce" in html.lower():
        result["platform"] = "WooCommerce"
    elif "bigcommerce" in html.lower():
        result["platform"] = "BigCommerce"
    elif "magento" in html.lower():
        result["platform"] = "Magento"

    prices = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            for field in ["price", "lowPrice", "highPrice"]:
                val = (data.get(field) or {}) if isinstance(data, dict) else None
                if val:
                    try:
                        prices.append(float(str(val).replace(",", "")))
                    except Exception:
                        pass
        except Exception:
            pass

    price_pattern = re.compile(r'[\$£€]\s?(\d{1,4}(?:[,\.]\d{2,3})?)')
    for p in price_pattern.findall(html)[:200]:
        try:
            v = float(p.replace(",", ""))
            if 1.0 <= v <= 5000.0:
                prices.append(v)
        except Exception:
            pass

    if prices:
        prices = sorted(set(prices))
        avg = round(sum(prices) / len(prices), 2)
        result["price_range"] = {"min": round(min(prices), 2), "max": round(max(prices), 2), "avg": avg, "count": len(prices)}
        result["aov_estimate"] = f"${round(avg * 1.2)}–${round(avg * 1.7)}"
        result["aov_confidence"] = "medium" if len(prices) >= 5 else "low"
        result["signals"].append(f"Extracted {len(prices)} price points (avg ${avg})")
        if avg >= 150:
            result["volume_tier"] = "Premium DTC"
            result["annual_order_estimate"] = "5K–50K orders/yr"
            result["revenue_tier"] = "$1M–$10M+ GMV"
        elif avg >= 60:
            result["volume_tier"] = "Mid Volume"
            result["annual_order_estimate"] = "10K–100K orders/yr"
            result["revenue_tier"] = "$500K–$5M GMV"
        elif avg >= 25:
            result["volume_tier"] = "High Volume"
            result["annual_order_estimate"] = "50K–500K orders/yr"
            result["revenue_tier"] = "$1M–$20M GMV"
        else:
            result["volume_tier"] = "Very High Volume"
            result["annual_order_estimate"] = "100K+ orders/yr"
            result["revenue_tier"] = "$2M–$30M+ GMV"

    if "shopify plus" in html.lower():
        result["platform"] = "Shopify Plus"
        result["signals"].append("Shopify Plus detected — typically $1M+ GMV")

    review_pattern = re.compile(r'(\d[\d,]+)\s*(?:reviews?|ratings?)', re.IGNORECASE)
    reviews = [int(m.replace(",", "")) for m in review_pattern.findall(html)]
    if reviews:
        result["signals"].append(f"Review signal: up to {max(reviews):,} reviews")

    return result


def get_copy(brand, poc_name, poc_title, protection, metrics, variant="A"):
    first = poc_name.split()[0] if poc_name else "there"
    has_comp = bool(protection.get("found"))
    competitor = protection["found"][0]["app"] if has_comp else None
    scenario = "has_competitor" if has_comp else "no_protection"

    templates = {
        "has_competitor": {
            "dm_A": (
                f"{first}, noticed {brand} uses {competitor} for shipping protection. "
                f"Parcelis offers merchants a different model — the infrastructure handles claims automatically, "
                f"no merchant involvement. Worth a quick look if you’re evaluating options?"
            ),
            "dm_B": (
                f"{first} — with {brand} running shipping protection already, "
                f"you clearly value post-purchase experience. Parcelis takes a different approach: "
                f"zero-ops resolution in 5–7 days, backed by The Hartford. Open to comparing notes?"
            ),
            "sub_A": f"Parcelis vs {competitor} — quick note",
            "sub_B": "Different model for shipping protection",
            "body_A": (
                f"Hi {first},\n\n"
                f"Noticed {brand} is using {competitor} for shipping protection.\n\n"
                f"Parcelis takes a different approach — institutionally backed (The Hartford), "
                f"zero-ops resolution in 5–7 days. Merchants never touch a claim.\n\n"
                f"Worth a 15-minute comparison if you’re reviewing your stack?\n\n"
                f"Sandeep\nVP Partnerships, Parcelis"
            ),
            "body_B": (
                f"Hi {first},\n\n"
                f"I head partnerships at Parcelis — we’re the revenue infrastructure layer "
                f"behind shipping protection for Shopify merchants.\n\n"
                f"{brand} already has protection in place, which tells me post-purchase experience matters to you. "
                f"Happy to share how our resolution model compares — no pitch, just a quick comparison.\n\n"
                f"Would a 15-min call make sense?\n\nSandeep | myparcelis.com"
            ),
        },
        "no_protection": {
            "dm_A": (
                f"{first}, every lost or damaged shipment at {brand} is silently eating margin. "
                f"Parcelis converts that liability into an automated resolution layer — no claims work for your team. "
                f"Worth 10 minutes to see how it works?"
            ),
            "dm_B": (
                f"{first} — {brand} looks like it’s doing real volume. "
                f"The silent cost most operators undercount: shipping failures hitting support queues. "
                f"Parcelis routes that to a 5–7 day resolution system. Could be relevant — open to a quick look?"
            ),
            "sub_A": f"Shipping failures → silent margin leak at {brand}",
            "sub_B": f"Zero-ops resolution for {brand}",
            "body_A": (
                f"Hi {first},\n\n"
                f"{brand} is driving real volume — and every lost or damaged shipment "
                f"is landing in your support queue, draining margin silently.\n\n"
                f"Parcelis installs an automated resolution layer: 5–7 day claim turnaround, "
                f"backed by The Hartford, zero merchant involvement.\n\n"
                f"Can I show you how it works for a store at {brand}’s scale?\n\n"
                f"Sandeep\nVP Partnerships, Parcelis | myparcelis.com"
            ),
            "body_B": (
                f"Hi {first},\n\n"
                f"I head partnerships at Parcelis. We work with Shopify merchants to convert "
                f"shipping liability into a zero-ops resolution system.\n\n"
                f"For {brand}: no claims management, no customer friction, "
                f"Hartford-backed coverage. Revenue infrastructure — not an app add-on.\n\n"
                f"Worth 15 minutes?\n\nSandeep | myparcelis.com"
            ),
        },
    }

    t = templates[scenario]
    if variant == "A":
        return {"dm": t["dm_A"], "subject": t["sub_A"], "body": t["body_A"], "scenario": scenario}
    else:
        return {"dm": t["dm_B"], "subject": t["sub_B"], "body": t["body_B"], "scenario": scenario}


# ── Revenue uplift engine ─────────────────────────────────────

def parcelis_tier_cost(aov: float) -> float:
    """
    Parcelis pricing tiers:
      AOV $0-$200   → $2.50/order (base)
      AOV $200-$400 → $4.00/order (+$1.50)
      AOV $400-$600 → $5.50/order (+$1.50 again)
      ... +$1.50 per additional $200 band
    """
    if aov <= 200:
        return 2.50
    extra_bands = int((aov - 200) / 200) + 1
    return round(2.50 + (1.50 * extra_bands), 2)


def parse_annual_orders_low(orders_str: str) -> int:
    """
    Parse conservative (low) end from strings like '50K-500K orders/yr' or '10K-100K orders/yr'.
    Returns integer. Returns None if unparseable.
    """
    if not orders_str:
        return None
    # Find all numbers with optional K/M suffix
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*([KkMm]?)', orders_str)
    values = []
    for num, suffix in matches:
        v = float(num)
        if suffix.upper() == 'K':
            v *= 1_000
        elif suffix.upper() == 'M':
            v *= 1_000_000
        if v >= 1:
            values.append(int(v))
    if not values:
        return None
    return min(values)  # conservative low-end


def parse_aov_midpoint(aov_str: str) -> float:
    """
    Parse midpoint from strings like '$34-$48' or '$120-$200'.
    Returns float or None.
    """
    if not aov_str:
        return None
    nums = re.findall(r'\$?(\d+)', aov_str)
    if len(nums) >= 2:
        return (float(nums[0]) + float(nums[1])) / 2
    if len(nums) == 1:
        return float(nums[0])
    return None


def calculate_revenue_uplift(metrics: dict) -> dict:
    """
    Calculates net revenue uplift from adding Parcelis shipping protection.

    Model:
      - Merchant charges buyer 5% of AOV as the protection fee
      - Parcelis cost = tier-based (see parcelis_tier_cost)
      - Net per order = buyer charge - Parcelis cost
      - Annual uplift = net per order x conservative annual order count
      - % GMV lift  = net per order / AOV x 100

    Returns None fields where data is insufficient.
    """
    aov = parse_aov_midpoint(metrics.get("aov_estimate"))
    annual_orders = parse_annual_orders_low(metrics.get("annual_order_estimate"))

    if aov is None:
        return {
            "viable": False,
            "reason": "AOV could not be estimated from site data",
            "aov": None,
        }

    cost = parcelis_tier_cost(aov)
    buyer_charge = round(aov * 0.05, 2)
    net_per_order = round(buyer_charge - cost, 2)
    pct_gmv_lift = round((net_per_order / aov) * 100, 2) if aov > 0 else 0

    if net_per_order <= 0:
        return {
            "viable": False,
            "reason": f"At AOV ~${aov:.0f}, the 5% buyer charge (${buyer_charge}) does not exceed Parcelis cost (${cost}). AOV needs to be above ~$50 for positive margin.",
            "aov": aov,
            "parcelis_cost": cost,
            "buyer_charge": buyer_charge,
            "net_per_order": net_per_order,
        }

    result = {
        "viable": True,
        "aov": aov,
        "parcelis_cost": cost,
        "buyer_charge": buyer_charge,
        "net_per_order": net_per_order,
        "pct_gmv_lift": pct_gmv_lift,
        "annual_orders_used": annual_orders,
        "annual_uplift": round(net_per_order * annual_orders) if annual_orders else None,
        "annual_uplift_formatted": None,
        "pct_lift_display": f"{pct_gmv_lift:.1f}%",
        "tier_label": (
            f"Base tier ($2.50/order)" if aov <= 200
            else f"${cost:.2f}/order tier (AOV ${int((int((aov-200)/200))*200)}-${int((int((aov-200)/200)+1)*200)})"
        ),
    }

    if result["annual_uplift"] is not None:
        u = result["annual_uplift"]
        result["annual_uplift_formatted"] = f"${u:,.0f}"

    return result


def get_uplift_copy(brand: str, poc_name: str, uplift: dict) -> dict:
    """
    Variant C — Revenue Uplift led.
    Uses actual calculated numbers in the DM and email body.
    Only generated when uplift is viable.
    """
    first = poc_name.split()[0] if poc_name else "there"

    if not uplift or not uplift.get("viable"):
        return None

    aov = uplift["aov"]
    net = uplift["net_per_order"]
    pct = uplift["pct_lift_display"]
    annual = uplift.get("annual_uplift_formatted")
    orders = uplift.get("annual_orders_used")
    buyer_charge = uplift["buyer_charge"]
    cost = uplift["parcelis_cost"]

    # Build the revenue line for the DM (keep under 300 chars)
    if annual:
        rev_line = f"~{annual}/yr in net revenue at {orders:,} orders"
    else:
        rev_line = f"~${net:.2f} net per order — a {pct} lift on GMV"

    dm = (
        f"{first}, at {brand}'s order volume: charging buyers {pct} of order value for protection nets "
        f"~${net:.2f}/order after Parcelis costs — {rev_line}. Zero ops changes. Worth 10 minutes to see the model?"
    )

    subject = f"Revenue uplift model for {brand}"

    body_lines = [
        f"Hi {first},",
        "",
        f"Running a quick model on {brand}:",
        "",
        f"  - Buyer protection charge:  5% of AOV = ~${buyer_charge:.2f}/order",
        f"  - Parcelis infrastructure:  ${cost:.2f}/order",
        f"  - Net to {brand}:           ~${net:.2f}/order ({pct} of GMV)",
    ]
    if annual and orders:
        body_lines += [
            f"  - At {orders:,} orders/yr:    {annual} in additional revenue",
        ]
    body_lines += [
        "",
        "Zero operational changes. Automated resolution in 5-7 days. Backed by The Hartford.",
        "",
        f"Happy to walk through the full model for {brand}'s actual numbers — takes 15 minutes.",
        "",
        "Sandeep\nVP Partnerships, Parcelis | myparcelis.com",
    ]

    return {
        "dm": dm,
        "subject": subject,
        "body": "\n".join(body_lines),
        "scenario": "revenue_uplift",
        "uplift": uplift,
    }


def get_contact_suggestion(poc_title, brand):
    title_lower = (poc_title or "").lower()
    priority = 99
    for kw, p in TITLE_PRIORITY.items():
        if kw in title_lower:
            priority = min(priority, p)
    if priority == 99:
        priority = 5

    if priority == 1:
        reasoning = f"{poc_title} is the ideal decision-maker. No escalation needed."
        suggestions = []
    elif priority <= 3:
        reasoning = f"{poc_title} has influence but may need Founder/CEO sign-off for new partnerships."
        suggestions = [
            {"title": "Founder / Co-Founder", "why": "Final authority on revenue partnerships",
             "search": f'"{brand}" founder site:linkedin.com'},
            {"title": "Head of Ecommerce / Operations", "why": "Owns the post-purchase stack",
             "search": f'"{brand}" head ecommerce site:linkedin.com'},
        ]
    else:
        reasoning = f"{poc_title or 'This contact'} is unlikely the final decision-maker. Find Founder or Head of Ops."
        suggestions = [
            {"title": "Founder / Co-Founder", "why": "Final call on new tech partnerships",
             "search": f'"{brand}" founder site:linkedin.com'},
            {"title": "Head of Ecommerce / Operations", "why": "Manages post-purchase stack directly",
             "search": f'"{brand}" head ecommerce operations site:linkedin.com'},
            {"title": "VP / Head of Growth", "why": "Revenue-minded — GMV angle resonates",
             "search": f'"{brand}" VP growth site:linkedin.com'},
        ]
    return {"priority": priority, "reasoning": reasoning, "suggestions": suggestions}


def run_full_workflow(entry: dict) -> dict:
    url = entry.get("url", "").strip()
    brand = entry.get("brand_name") or urlparse(url).netloc.replace("www.", "")
    poc_name = entry.get("poc_name", "")
    poc_title = entry.get("poc_title", "")

    protection = scan_protection_apps(url)
    metrics = estimate_metrics(url, brand)
    copy_a = get_copy(brand, poc_name, poc_title, protection, metrics, "A")
    copy_b = get_copy(brand, poc_name, poc_title, protection, metrics, "B")
    uplift = calculate_revenue_uplift(metrics)
    copy_c = get_uplift_copy(brand, poc_name, uplift)
    contact = get_contact_suggestion(poc_title, brand)

    return {
        "timestamp": datetime.now().isoformat(),
        "brand": brand,
        "url": url,
        "poc": {"name": poc_name, "title": poc_title,
                "linkedin": entry.get("poc_linkedin", ""),
                "email": entry.get("poc_email", "")},
        "protection": protection,
        "metrics": metrics,
        "uplift": uplift,
        "copy_a": copy_a,
        "copy_b": copy_b,
        "copy_c": copy_c,
        "contact": contact,
    }


# ════════════════════════════════════════════════════════════════
#  RENDER HELPERS
# ════════════════════════════════════════════════════════════════

def initials(name):
    if not name:
        return "??"
    parts = name.strip().split()
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


def render_pipeline(step):
    steps = [
        ("1", "Protection scan", "Route, Navidium…"),
        ("2", "Business metrics", "AOV + volume tier"),
        ("3", "Outreach copy", "LinkedIn + email A/B"),
        ("4", "Contact quality", "Better POC suggestion"),
    ]
    html = '<div class="pipeline-bar">'
    for i, (num, label, sub) in enumerate(steps, 1):
        cls = "active" if i == step else ("done" if i < step else "")
        icon = "✓" if cls == "done" else num
        html += f"""
        <div class="pipe-step">
            <div class="pipe-num {cls}">{icon}</div>
            <div class="pipe-label"><strong>{label}</strong>{sub}</div>
        </div>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_result(r):
    brand = r["brand"]
    protection = r["protection"]
    metrics = r["metrics"]
    uplift = r.get("uplift", {})
    copy_a = r["copy_a"]
    copy_b = r["copy_b"]
    copy_c = r.get("copy_c")
    contact = r["contact"]
    poc = r["poc"]

    # Header row
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {brand}")
        st.caption(f"{r['url']}  ·  POC: {poc['name'] or 'N/A'} ({poc['title'] or 'N/A'})")
    with col2:
        if metrics["platform"] != "Unknown":
            st.markdown(f'<span class="badge-platform">{metrics["platform"]}</span>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📦 Protection scan", "📊 Metrics + Revenue uplift", "✉ Outreach copy", "👤 Contact quality"])

    # ── Tab 1: Protection Scan
    with tab1:
        if protection.get("error"):
            st.warning(f"Could not scan site: {protection['error']}")
        elif protection["found"]:
            st.markdown("**Apps detected:**")
            for app in protection["found"]:
                st.markdown(
                    f'<span class="badge-detected">⚠ {app["app"]} — {app["count"]} signal{"s" if app["count"] > 1 else ""}</span>',
                    unsafe_allow_html=True,
                )
            st.info(
                "This merchant already uses shipping protection. Use the **competitor-aware copy** variant — "
                "acknowledge their existing setup and differentiate on Parcelis's zero-ops model and Hartford backing.",
                icon="💡",
            )
            if protection.get("signals"):
                with st.expander("Raw signals"):
                    for s in protection["signals"]:
                        st.caption(f"• {s}")
        else:
            st.markdown('<span class="badge-clear">✓ No protection app detected</span>', unsafe_allow_html=True)
            st.success(
                "Strong Parcelis opportunity. This merchant is unprotected — every lost or damaged shipment "
                "hits their support queue. Use the **margin-leak angle** in your outreach.",
                icon="🎯",
            )

    # ── Tab 2: Metrics
    with tab2:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="metric-box">
                <div class="label">Est. AOV</div>
                <div class="value">{metrics.get("aov_estimate") or "N/A"}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-box">
                <div class="label">Annual orders</div>
                <div class="value small">{metrics.get("annual_order_estimate") or "N/A"}</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-box">
                <div class="label">Revenue tier</div>
                <div class="value small">{metrics.get("revenue_tier") or "N/A"}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c4, c5 = st.columns(2)
        with c4:
            st.markdown(f"""<div class="metric-box">
                <div class="label">Volume tier</div>
                <div class="value small">{metrics.get("volume_tier") or "N/A"}</div>
            </div>""", unsafe_allow_html=True)
        with c5:
            pr = metrics.get("price_range", {})
            avg = pr.get("avg", "N/A")
            count = pr.get("count", 0)
            st.markdown(f"""<div class="metric-box">
                <div class="label">Avg product price</div>
                <div class="value small">${avg} <span style="font-size:0.7rem;color:#6c757d;">({count} points)</span></div>
            </div>""", unsafe_allow_html=True)

        if metrics.get("signals"):
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("Signals used"):
                for s in metrics["signals"]:
                    st.caption(f"• {s}")

        conf = metrics.get("aov_confidence", "low")
        conf_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf, "🔴")
        st.caption(f"{conf_color} AOV confidence: **{conf}** — for higher accuracy, check Similarweb or brand press coverage.")

        # ── Revenue uplift model ─────────────────────────────
        st.markdown("---")
        st.markdown("#### Revenue uplift model")
        st.caption("Assumes merchant charges buyers 5% of AOV · Parcelis tiered pricing · Conservative (low-end) order volume")

        if not uplift or uplift.get("aov") is None:
            st.warning("AOV data insufficient to calculate uplift. Run the live scanner for price data.")
        elif not uplift.get("viable"):
            st.warning(f"⚠ {uplift.get('reason', 'Uplift not viable at this AOV.')}")
        else:
            u = uplift
            col_u1, col_u2, col_u3, col_u4 = st.columns(4)
            with col_u1:
                st.markdown(f"""<div class="metric-box">
                    <div class="label">Buyer charge / order</div>
                    <div class="value">${u['buyer_charge']:.2f}</div>
                </div>""", unsafe_allow_html=True)
            with col_u2:
                st.markdown(f"""<div class="metric-box">
                    <div class="label">Parcelis cost / order</div>
                    <div class="value">${u['parcelis_cost']:.2f}</div>
                </div>""", unsafe_allow_html=True)
            with col_u3:
                st.markdown(f"""<div class="metric-box">
                    <div class="label">Net / order</div>
                    <div class="value" style="color:#28a745;">${u['net_per_order']:.2f}</div>
                </div>""", unsafe_allow_html=True)
            with col_u4:
                st.markdown(f"""<div class="metric-box">
                    <div class="label">% GMV lift</div>
                    <div class="value" style="color:#0056D2;">{u['pct_lift_display']}</div>
                </div>""", unsafe_allow_html=True)

            if u.get("annual_uplift_formatted") and u.get("annual_orders_used"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.success(
                    f"At **{u['annual_orders_used']:,} orders/yr** (conservative estimate): "
                    f"**{u['annual_uplift_formatted']}** in net annual revenue — "
                    f"a **{u['pct_lift_display']}** lift on GMV. "
                    f"Pricing tier: {u['tier_label']}.",
                    icon="📈",
                )
            else:
                st.info(f"Net margin per protected order: **${u['net_per_order']:.2f}** ({u['pct_lift_display']} of GMV). Annual order volume needed for total uplift estimate.")

            with st.expander("How this is calculated"):
                st.markdown(f"""
**Parcelis pricing tiers** (cost to merchant):
- AOV $0–$200 → **$2.50/order**
- AOV $200–$400 → **$4.00/order** ($2.50 + $1.50)
- AOV $400–$600 → **$5.50/order** ($2.50 + $1.50 × 2)
- Each additional $200 band adds $1.50

**This merchant ({brand})**:
- Estimated AOV midpoint: **~${u['aov']:.0f}**
- Parcelis cost at this AOV: **${u['parcelis_cost']:.2f}/order** ({u['tier_label']})
- Buyer charge at 5% of AOV: **${u['buyer_charge']:.2f}/order**
- Net revenue per protected order: **${u['net_per_order']:.2f}** ({u['pct_lift_display']} of GMV)
""")

    # ── Tab 3: Outreach Copy
    with tab3:
        variant_options = ["A — insight-led", "B — outcome-led"]
        if copy_c:
            variant_options.append("C — revenue uplift (uses live numbers)")

        variant = st.radio(
            "Variant",
            variant_options,
            horizontal=True,
            key=f"var_{brand}",
        )

        if variant.startswith("A"):
            v_key, copy = "A", copy_a
        elif variant.startswith("B"):
            v_key, copy = "B", copy_b
        else:
            v_key, copy = "C", copy_c

        if v_key != "C":
            scenario_label = "Competitor-aware" if copy["scenario"] == "has_competitor" else "No-protection"
            st.caption(f"Scenario: **{scenario_label}** · Variant **{v_key}**")
        else:
            u = uplift
            st.info(
                f"Revenue uplift variant — uses live math: **${u['net_per_order']:.2f}/order net**, "
                f"**{u['pct_lift_display']} GMV lift**"
                + (f", **{u['annual_uplift_formatted']}/yr**" if u.get("annual_uplift_formatted") else ""),
                icon="📈",
            )

        st.markdown("**LinkedIn DM**")
        dm_val = copy["dm"] if copy else ""
        st.text_area("", value=dm_val, height=110, key=f"li_{brand}_{v_key}", label_visibility="collapsed")
        if v_key == "C":
            char_count = len(dm_val)
            color = "🟢" if char_count <= 300 else "🔴"
            st.caption(f"{color} {char_count}/300 chars")

        st.markdown("**Email subject**")
        st.text_input("", value=copy.get("subject", ""), key=f"sub_{brand}_{v_key}", label_visibility="collapsed")

        st.markdown("**Email body**")
        st.text_area("", value=copy.get("body", ""), height=220, key=f"body_{brand}_{v_key}", label_visibility="collapsed")

        if v_key == "C":
            st.caption("💡 Variant C uses the live revenue model — update numbers if you have more accurate AOV/volume data.")
        else:
            st.caption("💡 All copy follows Parcelis tone rules: no em-dashes, no revenue angle in touch 1, no insurance framing.")

    # ── Tab 4: Contact Quality
    with tab4:
        stars = "★" * max(1, 6 - contact["priority"]) + "☆" * min(4, contact["priority"] - 1)
        ini = initials(poc["name"])
        st.markdown(f"""
        <div class="contact-row">
            <div class="contact-avatar">{ini}</div>
            <div>
                <div class="contact-name">{poc["name"] or "Unknown"}</div>
                <div class="contact-title">{poc["title"] or "Unknown title"}</div>
                <div style="color:#0056D2;font-size:0.9rem;margin:4px 0;">{stars}</div>
                <div class="contact-reason">{contact["reasoning"]}</div>
            </div>
        </div>""", unsafe_allow_html=True)

        if poc.get("linkedin"):
            st.link_button("Open LinkedIn profile ↗", poc["linkedin"])

        if contact["suggestions"]:
            st.markdown("**Better contacts to find:**")
            for s in contact["suggestions"]:
                st.markdown(f"""
                <div class="suggest-row">
                    <div style="font-size:1.2rem;">🔍</div>
                    <div>
                        <div class="suggest-title">{s["title"]}</div>
                        <div class="suggest-why">{s["why"]}</div>
                        <div class="suggest-search">{s["search"]}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
                st.link_button(
                    f"Search LinkedIn for {s['title'].split('/')[0].strip()} ↗",
                    f"https://www.google.com/search?q={requests.utils.quote(s['search'])}",
                    use_container_width=True,
                )



def results_to_csv(results):
    rows = []
    for r in results:
        u = r.get("uplift") or {}
        cc = r.get("copy_c") or {}
        rows.append({
            "brand": r["brand"],
            "url": r["url"],
            "poc_name": r["poc"]["name"],
            "poc_title": r["poc"]["title"],
            "poc_linkedin": r["poc"]["linkedin"],
            "poc_email": r["poc"]["email"],
            "platform": r["metrics"]["platform"],
            "protection_detected": ", ".join(a["app"] for a in r["protection"].get("found", [])),
            "aov_estimate": r["metrics"].get("aov_estimate"),
            "volume_tier": r["metrics"].get("volume_tier"),
            "annual_order_estimate": r["metrics"].get("annual_order_estimate"),
            "revenue_tier": r["metrics"].get("revenue_tier"),
            "uplift_viable": u.get("viable", False),
            "uplift_aov_midpoint": "${:.0f}".format(u["aov"]) if u.get("aov") else "",
            "uplift_parcelis_cost": "${:.2f}".format(u["parcelis_cost"]) if u.get("parcelis_cost") else "",
            "uplift_buyer_charge": "${:.2f}".format(u["buyer_charge"]) if u.get("buyer_charge") else "",
            "uplift_net_per_order": "${:.2f}".format(u["net_per_order"]) if u.get("net_per_order") else "",
            "uplift_pct_gmv_lift": u.get("pct_lift_display", ""),
            "uplift_annual_revenue": u.get("annual_uplift_formatted", ""),
            "uplift_tier_label": u.get("tier_label", ""),
            "scenario": r["copy_a"]["scenario"],
            "linkedin_dm_A": r["copy_a"]["dm"],
            "email_subject_A": r["copy_a"]["subject"],
            "email_body_A": r["copy_a"]["body"].replace("\n", " | "),
            "linkedin_dm_B": r["copy_b"]["dm"],
            "email_subject_B": r["copy_b"]["subject"],
            "email_body_B": r["copy_b"]["body"].replace("\n", " | "),
            "linkedin_dm_C": cc.get("dm", ""),
            "email_subject_C": cc.get("subject", ""),
            "email_body_C": cc.get("body", "").replace("\n", " | ") if cc.get("body") else "",
            "contact_priority": r["contact"]["priority"],
            "contact_reasoning": r["contact"]["reasoning"],
            "suggested_roles": " | ".join(s["title"] for s in r["contact"]["suggestions"]),
        })
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h2>📦 Parcelis Scanner</h2>
        <p>Outreach intelligence pipeline</p>
    </div>
    """, unsafe_allow_html=True)

    mode = st.radio("Mode", ["Single lead", "CSV batch"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**What this scans for:**")
    for app in PROTECTION_APPS:
        st.caption(f"• {app}")

    st.markdown("---")
    st.markdown("**Revenue uplift model:**")
    st.caption("• Buyer charge: 5% of AOV")
    st.caption("• Tier 1 (AOV ≤$200): $2.50/order")
    st.caption("• Tier 2 (AOV $200-400): $4.00/order")
    st.caption("• Tier 3 (AOV $400-600): $5.50/order")
    st.caption("• +$1.50 per $200 band above")

    st.markdown("---")
    st.markdown("**Copy rules enforced:**")
    st.caption("• No em-dashes")
    st.caption("• No insurance framing")
    st.caption("• Revenue angle: touch 2+ only")
    st.caption("• DM ≤300 chars (Variant C checked)")
    st.caption("• Email body ≤120 words")

    st.markdown("---")
    st.caption("Sandeep Trivedi · VP Partnerships  \n[myparcelis.com](https://myparcelis.com)")


# ════════════════════════════════════════════════════════════════
#  MAIN PAGE
# ════════════════════════════════════════════════════════════════

st.markdown("""
<div class="parcelis-header">
    <div>
        <h1>Parcelis Outreach Scanner</h1>
        <p>4-agent pipeline: scan → research → draft → suggest · Revenue uplift model v2</p>
    </div>
    <span class="header-badge">v2.0</span>
</div>
""", unsafe_allow_html=True)


# ── SINGLE LEAD MODE ─────────────────────────────────────────
if mode == "Single lead":
    with st.form("single_form"):
        st.markdown("#### Store details")
        c1, c2 = st.columns([2, 1])
        with c1:
            url = st.text_input("Store URL", placeholder="https://brand.com")
        with c2:
            brand_name = st.text_input("Brand name", placeholder="Auto-detected")

        st.markdown("#### POC info")
        c3, c4 = st.columns(2)
        with c3:
            poc_name = st.text_input("Full name", placeholder="Jane Smith")
            poc_linkedin = st.text_input("LinkedIn URL", placeholder="https://linkedin.com/in/...")
        with c4:
            poc_title = st.text_input("Job title", placeholder="Co-Founder")
            poc_email = st.text_input("Email", placeholder="jane@brand.com")

        submitted = st.form_submit_button("▶ Run workflow + revenue uplift", use_container_width=True, type="primary")

    if submitted and url:
        if not url.startswith("http"):
            url = "https://" + url

        pipeline_placeholder = st.empty()
        progress_bar = st.progress(0)
        status = st.empty()

        brand_resolved = brand_name or urlparse(url).netloc.replace("www.", "")

        with pipeline_placeholder:
            render_pipeline(1)
        status.info("Agent 1 — scanning for shipping protection apps...")
        progress_bar.progress(15)
        protection = scan_protection_apps(url)

        with pipeline_placeholder:
            render_pipeline(2)
        status.info("Agent 2 — researching business metrics...")
        progress_bar.progress(40)
        metrics = estimate_metrics(url, brand_resolved)

        with pipeline_placeholder:
            render_pipeline(3)
        status.info("Agent 3 — calculating revenue uplift + drafting copy (A/B/C)...")
        progress_bar.progress(65)
        uplift = calculate_revenue_uplift(metrics)
        copy_a = get_copy(brand_resolved, poc_name, poc_title, protection, metrics, "A")
        copy_b = get_copy(brand_resolved, poc_name, poc_title, protection, metrics, "B")
        copy_c = get_uplift_copy(brand_resolved, poc_name, uplift)
        time.sleep(0.3)

        with pipeline_placeholder:
            render_pipeline(4)
        status.info("Agent 4 — evaluating contact quality...")
        progress_bar.progress(90)
        contact = get_contact_suggestion(poc_title, brand_resolved)
        time.sleep(0.2)

        progress_bar.progress(100)
        status.success("Pipeline complete — revenue uplift model included.")
        time.sleep(0.5)
        progress_bar.empty()
        status.empty()

        result = {
            "timestamp": datetime.now().isoformat(),
            "brand": brand_resolved,
            "url": url,
            "poc": {"name": poc_name, "title": poc_title, "linkedin": poc_linkedin, "email": poc_email},
            "protection": protection,
            "metrics": metrics,
            "uplift": uplift,
            "copy_a": copy_a,
            "copy_b": copy_b,
            "copy_c": copy_c,
            "contact": contact,
        }

        st.markdown("---")
        st.markdown("### Results")
        render_result(result)

        csv_data = results_to_csv([result])
        st.download_button(
            "⬇ Download results CSV",
            data=csv_data,
            file_name=f"parcelis_{brand_resolved.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    elif submitted:
        st.warning("Please enter a store URL.")


# ── CSV BATCH MODE ────────────────────────────────────────────
else:
    st.markdown("#### Upload your leads CSV")
    st.caption("Required: `url`, `brand_name`, `poc_name`, `poc_title`  ·  Optional: `poc_linkedin`, `poc_email`")

    sample_csv = """url,brand_name,poc_name,poc_title,poc_linkedin,poc_email
https://www.beardbrand.com,Beardbrand,Eric Bandholz,Founder,https://linkedin.com/in/ericbandholz,eric@beardbrand.com
https://www.huckberry.com,Huckberry,Richard Greiner,Co-Founder,https://linkedin.com/in/richardgreiner,
https://www.chubbiesshorts.com,Chubbies,Tom Montgomery,Co-Founder,,
"""
    st.download_button(
        "⬇ Download sample CSV template",
        data=sample_csv,
        file_name="parcelis_leads_template.csv",
        mime="text/csv",
    )

    uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

    if uploaded:
        content = uploaded.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        rows = [r for r in reader if r.get("url")]

        st.success(f"Loaded **{len(rows)} lead{'s' if len(rows) != 1 else ''}** from {uploaded.name}")

        with st.expander("Preview leads"):
            for i, r in enumerate(rows[:10], 1):
                st.caption(f"{i}. {r.get('brand_name', r.get('url'))} — {r.get('poc_name', 'N/A')} ({r.get('poc_title', 'N/A')})")
            if len(rows) > 10:
                st.caption(f"... and {len(rows) - 10} more")

        if st.button("▶ Run batch pipeline + revenue uplift", type="primary", use_container_width=True):
            results = []
            pipeline_ph = st.empty()
            prog = st.progress(0)
            status = st.empty()

            for i, row in enumerate(rows):
                brand = row.get("brand_name") or urlparse(row.get("url", "")).netloc.replace("www.", "")
                status.info(f"Processing {i + 1}/{len(rows)}: **{brand}**")
                step_base = int((i / len(rows)) * 90)

                with pipeline_ph:
                    render_pipeline(1)
                prog.progress(step_base + 3)
                protection = scan_protection_apps(row.get("url", ""))

                with pipeline_ph:
                    render_pipeline(2)
                prog.progress(step_base + 8)
                metrics = estimate_metrics(row.get("url", ""), brand)

                with pipeline_ph:
                    render_pipeline(3)
                prog.progress(step_base + 16)
                uplift = calculate_revenue_uplift(metrics)
                copy_a = get_copy(brand, row.get("poc_name", ""), row.get("poc_title", ""), protection, metrics, "A")
                copy_b = get_copy(brand, row.get("poc_name", ""), row.get("poc_title", ""), protection, metrics, "B")
                copy_c = get_uplift_copy(brand, row.get("poc_name", ""), uplift)

                with pipeline_ph:
                    render_pipeline(4)
                prog.progress(step_base + 22)
                contact = get_contact_suggestion(row.get("poc_title", ""), brand)

                results.append({
                    "timestamp": datetime.now().isoformat(),
                    "brand": brand,
                    "url": row.get("url", ""),
                    "poc": {
                        "name": row.get("poc_name", ""),
                        "title": row.get("poc_title", ""),
                        "linkedin": row.get("poc_linkedin", ""),
                        "email": row.get("poc_email", ""),
                    },
                    "protection": protection,
                    "metrics": metrics,
                    "uplift": uplift,
                    "copy_a": copy_a,
                    "copy_b": copy_b,
                    "copy_c": copy_c,
                    "contact": contact,
                })
                time.sleep(0.4)

            prog.progress(100)
            status.success(f"Batch complete — {len(results)} leads processed with revenue uplift models.")
            pipeline_ph.empty()
            time.sleep(0.4)

            # ── Batch summary metrics
            st.markdown("---")
            detected = [r for r in results if r["protection"]["found"]]
            no_protection = [r for r in results if not r["protection"]["found"]]
            viable_uplift = [r for r in results if r.get("uplift", {}).get("viable")]
            ideal_contacts = [r for r in results if r["contact"]["priority"] == 1]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total leads", len(results))
            m2.metric("Unprotected (opportunity)", len(no_protection))
            m3.metric("Revenue uplift viable", len(viable_uplift))
            m4.metric("Ideal contact (Founder/CEO)", len(ideal_contacts))

            # Top uplift opportunities
            viable = [(r, r["uplift"]) for r in results if r.get("uplift", {}).get("annual_uplift")]
            if viable:
                viable.sort(key=lambda x: x[1]["annual_uplift"], reverse=True)
                st.markdown("#### Top revenue uplift opportunities")
                for rank, (r, u) in enumerate(viable[:3], 1):
                    st.markdown(
                        f"**{rank}. {r['brand']}** — {u['annual_uplift_formatted']}/yr · "
                        f"{u['pct_lift_display']} GMV lift · ${u['net_per_order']:.2f}/order net"
                    )

            st.markdown("### All results")
            tabs = st.tabs([r["brand"] for r in results])
            for tab, result in zip(tabs, results):
                with tab:
                    render_result(result)

            csv_out = results_to_csv(results)
            st.download_button(
                "⬇ Download full results CSV (with uplift + Variant C)",
                data=csv_out,
                file_name=f"parcelis_batch_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
