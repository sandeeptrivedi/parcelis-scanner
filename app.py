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

st.set_page_config(
    page_title="Parcelis Outreach Scanner",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background: #f8f9fa; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1100px; }
.parcelis-header { background: #0056D2; color: white; padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between; }
.parcelis-header h1 { font-size: 1.3rem; font-weight: 600; margin: 0; color: white; }
.parcelis-header p { font-size: 0.8rem; margin: 0; opacity: 0.8; }
.header-badge { background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; color: white; }
.pipeline-bar { display: flex; align-items: center; background: white; border: 1px solid #e9ecef; border-radius: 10px; padding: 1rem 1.5rem; margin-bottom: 1.5rem; gap: 0; }
.pipe-step { flex: 1; text-align: center; position: relative; }
.pipe-step:not(:last-child)::after { content: ''; position: absolute; top: 18px; right: 0; width: 100%; height: 1px; background: #dee2e6; z-index: 0; left: 50%; }
.pipe-num { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 600; margin: 0 auto 6px; position: relative; z-index: 1; border: 2px solid #dee2e6; background: white; color: #6c757d; }
.pipe-num.active { background: #0056D2; border-color: #0056D2; color: white; }
.pipe-num.done { background: #28a745; border-color: #28a745; color: white; }
.pipe-label { font-size: 0.72rem; color: #6c757d; line-height: 1.3; }
.pipe-label strong { display: block; color: #1a2b4a; font-size: 0.78rem; }
.metric-box { background: #f8f9fa; border-radius: 8px; padding: 0.85rem 1rem; text-align: center; }
.metric-box .label { font-size: 0.7rem; color: #6c757d; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }
.metric-box .value { font-size: 1.1rem; font-weight: 600; color: #1a2b4a; margin-top: 4px; }
.metric-box .value.small { font-size: 0.85rem; }
.badge-detected { display: inline-block; background: #fff3cd; color: #856404; border: 1px solid #ffc107; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; margin: 2px; }
.badge-clear { display: inline-block; background: #d1e7dd; color: #0f5132; border: 1px solid #28a745; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; }
.badge-platform { display: inline-block; background: #cfe2ff; color: #084298; border: 1px solid #0056D2; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; }
.contact-row { display: flex; align-items: flex-start; gap: 12px; background: #f8f9fa; border-radius: 8px; padding: 0.9rem; margin-bottom: 0.75rem; }
.contact-avatar { width: 40px; height: 40px; border-radius: 50%; background: #cfe2ff; color: #084298; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.8rem; flex-shrink: 0; }
.contact-name { font-weight: 600; font-size: 0.9rem; color: #1a2b4a; }
.contact-title { font-size: 0.8rem; color: #6c757d; }
.contact-reason { font-size: 0.8rem; color: #495057; margin-top: 6px; line-height: 1.5; }
.suggest-row { display: flex; align-items: flex-start; gap: 10px; border: 1px solid #e9ecef; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; background: white; }
.suggest-title { font-weight: 600; font-size: 0.875rem; color: #1a2b4a; }
.suggest-why { font-size: 0.8rem; color: #6c757d; margin-top: 2px; }
.suggest-search { font-size: 0.75rem; color: #0056D2; margin-top: 4px; }
.sidebar-brand { background: #0056D2; color: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; text-align: center; }
.sidebar-brand h2 { color: white; font-size: 1rem; margin: 0; }
.sidebar-brand p { color: rgba(255,255,255,0.75); font-size: 0.75rem; margin: 4px 0 0; }
.poc-card { border: 1px solid #e9ecef; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.75rem; background: white; }
.poc-card-header { font-size: 0.8rem; font-weight: 600; color: #0056D2; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem; }
.dm-suggestion { background: #f0f7ff; border: 1px solid #b8d4f8; border-radius: 8px; padding: 0.75rem; margin-bottom: 0.5rem; }
.dm-suggestion .dm-name { font-weight: 600; font-size: 0.875rem; color: #1a2b4a; }
.dm-suggestion .dm-title { font-size: 0.8rem; color: #6c757d; margin-top: 2px; }
div[data-testid="stForm"] { border: none; padding: 0; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  SCANNER ENGINE
# ════════════════════════════════════════════════════════════════

PROTECTION_APPS = {
    "Route": {"domains": ["route.com", "routeapp.io", "cdn.routeapp.io"], "keywords": ["route-widget", "route_order_protection", "RouteApp", "addRouteProtection"]},
    "Navidium": {"domains": ["navidium.com", "navidiumshipping.com"], "keywords": ["navidium", "navidium-protection", "NavidiumWidget"]},
    "ShipInsure": {"domains": ["shipinsure.com"], "keywords": ["shipinsure", "ShipInsure"]},
    "Corso": {"domains": ["corso.com", "corso-platform.com"], "keywords": ["corso-protection", "CorsoProtection"]},
    "Redo": {"domains": ["getredo.com", "redo.com"], "keywords": ["redo-protection", "ReDoProtection"]},
    "AfterShip Protection": {"domains": ["aftership.com"], "keywords": ["aftership-protection", "AfterShipProtection"]},
    "Seel": {"domains": ["seel.com"], "keywords": ["seel-protection", "SeelProtection"]},
    "Cover Genius": {"domains": ["covergenius.com", "xcover.com"], "keywords": ["covergenius", "xcover"]},
    "Extend": {"domains": ["helloextend.com", "extend.com"], "keywords": ["helloextend", "ExtendProtection"]},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TITLE_PRIORITY = {
    "founder": 1, "co-founder": 1, "ceo": 1, "coo": 2,
    "head of ecommerce": 2, "head of operations": 2, "head of growth": 2,
    "vp": 3, "director": 4, "manager": 5,
}


# ── Feature 1: Token-free brand name extraction ─────────────────
def extract_brand_name(url: str) -> str:
    """
    Extracts brand name from website using OG tags, schema.org, title tag.
    Zero LLM tokens — pure HTML parsing.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        soup = BeautifulSoup(r.text, "lxml")

        # 1. og:site_name — most reliable
        og = soup.find("meta", property="og:site_name")
        if og and og.get("content", "").strip():
            return og["content"].strip()

        # 2. schema.org Organization / Store name
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and item.get("@type") in ["Organization", "Store", "LocalBusiness", "WebSite"] and item.get("name"):
                        return item["name"].strip()
            except Exception:
                pass

        # 3. Title tag — take the first meaningful part before separator
        title = soup.find("title")
        if title and title.text.strip():
            t = title.text.strip()
            parts = re.split(r'\s*[\|\-–—·]\s*', t)
            for part in parts:
                part = part.strip()
                if len(part) > 2 and part.lower() not in {"home", "shop", "store", "official", "welcome", "homepage"}:
                    return part

        # 4. application-name meta
        app_meta = soup.find("meta", attrs={"name": "application-name"})
        if app_meta and app_meta.get("content", "").strip():
            return app_meta["content"].strip()

    except Exception:
        pass

    # Fallback: clean hostname
    host = urlparse(url).netloc.replace("www.", "").split(".")[0]
    return host.replace("-", " ").replace("_", " ").title()


# ── Feature 2: Decision maker suggestion — Google → LinkedIn ────
def find_decision_makers(brand_name: str) -> list:
    """
    Token-free: Google search for founder/CEO LinkedIn profiles.
    Parses result page HTML for LinkedIn URLs + names. Returns up to 3.
    """
    results = []
    try:
        query = f'"{brand_name}" (founder OR "co-founder" OR CEO OR "head of ecommerce") site:linkedin.com/in'
        r = requests.get(
            f"https://www.google.com/search?q={requests.utils.quote(query)}&num=6",
            headers=HEADERS, timeout=10,
        )
        # Extract LinkedIn slugs from raw HTML
        li_matches = re.findall(
            r'linkedin\.com/in/([a-zA-Z0-9\-]{3,60})(?:[&"/ ])',
            r.text,
        )
        seen = set()
        soup = BeautifulSoup(r.text, "lxml")

        for slug in li_matches:
            if slug in seen or slug in {"company", "pub", "in", "jobs"}:
                continue
            seen.add(slug)
            li_url = f"https://www.linkedin.com/in/{slug}"

            # Try to find the title element near this link in the DOM
            name, title = "", ""
            for a in soup.find_all("a", href=re.compile(re.escape(slug))):
                parent = a.find_parent("div")
                if parent:
                    h3 = parent.find("h3")
                    if h3:
                        raw = re.sub(r'\s*\|\s*LinkedIn\s*$', '', h3.text, flags=re.I).strip()
                        if " - " in raw:
                            parts = raw.split(" - ", 1)
                            name, title = parts[0].strip(), parts[1].strip()
                        else:
                            name = raw
                        break

            if not name:
                name = slug.replace("-", " ").title()

            results.append({"name": name, "title": title, "linkedin_url": li_url})
            if len(results) >= 3:
                break

    except Exception:
        pass
    return results


# ── Feature 3: LinkedIn public profile extractor ─────────────────
def extract_linkedin_info(linkedin_url: str) -> dict:
    """
    Token-free: parse OG meta tags from public LinkedIn profile.
    Returns name, title, summary. No login required for public profiles.
    """
    result = {"name": "", "title": "", "summary": "", "email": "", "error": None}
    if not linkedin_url or "linkedin.com" not in linkedin_url:
        result["error"] = "Not a LinkedIn URL"
        return result
    try:
        r = requests.get(linkedin_url, headers=HEADERS, timeout=12, allow_redirects=True)
        if r.status_code != 200:
            result["error"] = f"HTTP {r.status_code}"
            return result
        soup = BeautifulSoup(r.text, "lxml")

        # og:title → "Name - Title | LinkedIn"
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            raw = re.sub(r'\s*\|\s*LinkedIn\s*$', '', og_title["content"], flags=re.I).strip()
            if " - " in raw:
                parts = raw.split(" - ", 1)
                result["name"] = parts[0].strip()
                result["title"] = parts[1].strip()
            else:
                result["name"] = raw

        # og:description → headline / summary
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            result["summary"] = og_desc["content"][:180].strip()

        # Fallback: extract title from summary first sentence
        if not result["title"] and result["summary"]:
            first = result["summary"].split(".")[0].strip()
            if len(first) < 100:
                result["title"] = first

        # Email: sometimes visible on public profiles
        email_pat = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
        found_emails = email_pat.findall(r.text)
        public = [e for e in found_emails if not any(
            x in e.lower() for x in ["linkedin", "example", "sentry", "w3.org", "schema"]
        )]
        if public:
            result["email"] = public[0]

    except Exception as e:
        result["error"] = str(e)[:80]
    return result


# ── Core scanner functions ────────────────────────────────────────
def scan_protection_apps(url: str) -> dict:
    result = {"found": [], "confidence": "none", "signals": [], "pages_scanned": [], "error": None}
    for page in [url, url.rstrip("/") + "/cart"]:
        try:
            r = requests.get(page, headers=HEADERS, timeout=12, allow_redirects=True)
            if r.status_code == 200:
                result["pages_scanned"].append(page)
                html_lower = r.text.lower()
                for app_name, app_data in PROTECTION_APPS.items():
                    hits = [f"domain: {d}" for d in app_data["domains"] if d.lower() in html_lower]
                    hits += [f"keyword: {k}" for k in app_data["keywords"] if k.lower() in html_lower]
                    if hits:
                        existing = next((a for a in result["found"] if a["app"] == app_name), None)
                        if existing:
                            existing["signals"].extend(hits)
                            existing["count"] = len(existing["signals"])
                        else:
                            result["found"].append({"app": app_name, "signals": hits, "count": len(hits)})
        except Exception as e:
            result["signals"].append(f"Fetch error: {str(e)[:60]}")
    if result["found"]:
        result["confidence"] = "high" if max(a["count"] for a in result["found"]) >= 2 else "medium"
    elif not result["pages_scanned"]:
        result["error"] = "Could not fetch site"
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
    if "shopify plus" in html.lower():
        result["platform"] = "Shopify Plus"
        result["signals"].append("Shopify Plus detected")

    prices = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            for field in ["price", "lowPrice", "highPrice"]:
                val = data.get(field) if isinstance(data, dict) else None
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
        result["aov_estimate"] = f"${round(avg * 1.2)}-${round(avg * 1.7)}"
        result["aov_confidence"] = "medium" if len(prices) >= 5 else "low"
        result["signals"].append(f"Extracted {len(prices)} price points (avg ${avg})")
        if avg >= 150:
            result["volume_tier"] = "Premium DTC"
            result["annual_order_estimate"] = "5K-50K orders/yr"
            result["revenue_tier"] = "$1M-$10M+ GMV"
        elif avg >= 60:
            result["volume_tier"] = "Mid Volume"
            result["annual_order_estimate"] = "10K-100K orders/yr"
            result["revenue_tier"] = "$500K-$5M GMV"
        elif avg >= 25:
            result["volume_tier"] = "High Volume"
            result["annual_order_estimate"] = "50K-500K orders/yr"
            result["revenue_tier"] = "$1M-$20M GMV"
        else:
            result["volume_tier"] = "Very High Volume"
            result["annual_order_estimate"] = "100K+ orders/yr"
            result["revenue_tier"] = "$2M-$30M+ GMV"

    review_pattern = re.compile(r'(\d[\d,]+)\s*(?:reviews?|ratings?)', re.IGNORECASE)
    reviews = [int(m.replace(",", "")) for m in review_pattern.findall(html)]
    if reviews:
        result["signals"].append(f"Review signal: up to {max(reviews):,} reviews")
    return result


# ── Revenue uplift engine ────────────────────────────────────────
def parcelis_tier_cost(aov: float) -> float:
    if aov <= 200:
        return 2.50
    extra_bands = int((aov - 200) / 200) + 1
    return round(2.50 + (1.50 * extra_bands), 2)

def parse_aov_midpoint(s: str):
    nums = re.findall(r'\$?(\d+)', s or '')
    if len(nums) >= 2:
        return (float(nums[0]) + float(nums[1])) / 2
    if len(nums) == 1:
        return float(nums[0])
    return None

def parse_annual_orders_low(s: str):
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*([KkMm]?)', s or '')
    values = []
    for num, sfx in matches:
        v = float(num)
        if sfx.upper() == 'K': v *= 1_000
        elif sfx.upper() == 'M': v *= 1_000_000
        if v >= 1: values.append(int(v))
    return min(values) if values else None

def calculate_revenue_uplift(metrics: dict) -> dict:
    aov = parse_aov_midpoint(metrics.get("aov_estimate"))
    annual_orders = parse_annual_orders_low(metrics.get("annual_order_estimate"))
    if aov is None:
        return {"viable": False, "reason": "AOV could not be estimated from site data", "aov": None}
    cost = parcelis_tier_cost(aov)
    buyer_charge = round(aov * 0.05, 2)
    net_per_order = round(buyer_charge - cost, 2)
    pct_gmv_lift = round((net_per_order / aov) * 100, 2) if aov > 0 else 0
    if net_per_order <= 0:
        return {
            "viable": False,
            "reason": f"At AOV ~${aov:.0f}, the 5% buyer charge (${buyer_charge}) does not exceed Parcelis cost (${cost}). AOV needs to be above ~$50.",
            "aov": aov, "parcelis_cost": cost, "buyer_charge": buyer_charge, "net_per_order": net_per_order,
        }
    result = {
        "viable": True, "aov": aov, "parcelis_cost": cost,
        "buyer_charge": buyer_charge, "net_per_order": net_per_order,
        "pct_gmv_lift": pct_gmv_lift, "annual_orders_used": annual_orders,
        "annual_uplift": round(net_per_order * annual_orders) if annual_orders else None,
        "annual_uplift_formatted": None,
        "pct_lift_display": f"{pct_gmv_lift:.1f}%",
        "tier_label": f"Base tier ($2.50/order)" if aov <= 200 else f"${cost:.2f}/order tier",
    }
    if result["annual_uplift"] is not None:
        result["annual_uplift_formatted"] = f"${result['annual_uplift']:,.0f}"
    return result


# ── Copywriter ─────────────────────────────────────────────────
def get_copy(brand, poc_name, poc_title, protection, metrics, variant="A"):
    first = poc_name.split()[0] if poc_name else "there"
    has_comp = bool(protection.get("found"))
    competitor = protection["found"][0]["app"] if has_comp else None
    scenario = "has_competitor" if has_comp else "no_protection"

    templates = {
        "has_competitor": {
            "dm_A": f"{first}, noticed {brand} uses {competitor} for shipping protection. Parcelis offers merchants a different model - the infrastructure handles claims automatically, no merchant involvement. Worth a quick look if you're evaluating options?",
            "dm_B": f"{first} - with {brand} running shipping protection already, you clearly value post-purchase experience. Parcelis takes a different approach: zero-ops resolution in 5-7 days, backed by The Hartford. Open to comparing notes?",
            "sub_A": f"Parcelis vs {competitor} - quick note",
            "sub_B": "Different model for shipping protection",
            "body_A": f"Hi {first},\n\nNoticed {brand} is using {competitor} for shipping protection.\n\nParcelis takes a different approach - institutionally backed (The Hartford), zero-ops resolution in 5-7 days. Merchants never touch a claim.\n\nWorth a 15-minute comparison if you're reviewing your stack?\n\nSandeep\nVP Partnerships, Parcelis",
            "body_B": f"Hi {first},\n\nI head partnerships at Parcelis - we're the revenue infrastructure layer behind shipping protection for Shopify merchants.\n\n{brand} already has protection in place, which tells me post-purchase experience matters to you. Happy to share how our resolution model compares - no pitch, just a quick comparison.\n\nWould a 15-min call make sense?\n\nSandeep | myparcelis.com",
        },
        "no_protection": {
            "dm_A": f"{first}, every lost or damaged shipment at {brand} is silently eating margin. Parcelis converts that liability into an automated resolution layer - no claims work for your team. Worth 10 minutes to see how it works?",
            "dm_B": f"{first} - {brand} looks like it's doing real volume. The silent cost most operators undercount: shipping failures hitting support queues. Parcelis routes that to a 5-7 day resolution system. Could be relevant - open to a quick look?",
            "sub_A": f"Shipping failures - silent margin leak at {brand}",
            "sub_B": f"Zero-ops resolution for {brand}",
            "body_A": f"Hi {first},\n\n{brand} is driving real volume - and every lost or damaged shipment is landing in your support queue, draining margin silently.\n\nParcelis installs an automated resolution layer: 5-7 day claim turnaround, backed by The Hartford, zero merchant involvement.\n\nCan I show you how it works for a store at {brand}'s scale?\n\nSandeep\nVP Partnerships, Parcelis | myparcelis.com",
            "body_B": f"Hi {first},\n\nI head partnerships at Parcelis. We work with Shopify merchants to convert shipping liability into a zero-ops resolution system.\n\nFor {brand}: no claims management, no customer friction, Hartford-backed coverage. Revenue infrastructure - not an app add-on.\n\nWorth 15 minutes?\n\nSandeep | myparcelis.com",
        },
    }
    t = templates[scenario]
    if variant == "A":
        return {"dm": t["dm_A"], "subject": t["sub_A"], "body": t["body_A"], "scenario": scenario}
    return {"dm": t["dm_B"], "subject": t["sub_B"], "body": t["body_B"], "scenario": scenario}


def get_uplift_copy(brand: str, poc_name: str, uplift: dict):
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
    rev_line = f"~{annual}/yr in net revenue at {orders:,} orders" if annual else f"~${net:.2f} net per order - a {pct} lift on GMV"
    dm = f"{first}, at {brand}'s order volume: charging buyers {pct} of order value for protection nets ~${net:.2f}/order after Parcelis costs - {rev_line}. Zero ops changes. Worth 10 minutes to see the model?"
    body_lines = [
        f"Hi {first},", "",
        f"Running a quick model on {brand}:", "",
        f"  - Buyer protection charge:  5% of AOV = ~${buyer_charge:.2f}/order",
        f"  - Parcelis infrastructure:  ${cost:.2f}/order",
        f"  - Net to {brand}:           ~${net:.2f}/order ({pct} of GMV)",
    ]
    if annual and orders:
        body_lines.append(f"  - At {orders:,} orders/yr:    {annual} in additional revenue")
    body_lines += ["", "Zero operational changes. Automated resolution in 5-7 days. Backed by The Hartford.", "",
                   f"Happy to walk through the full model for {brand}'s actual numbers - takes 15 minutes.", "",
                   "Sandeep\nVP Partnerships, Parcelis | myparcelis.com"]
    return {"dm": dm, "subject": f"Revenue uplift model for {brand}", "body": "\n".join(body_lines), "scenario": "revenue_uplift"}


def get_contact_suggestion(poc_title, brand):
    title_lower = (poc_title or "").lower()
    priority = 99
    for kw, p in TITLE_PRIORITY.items():
        if kw in title_lower:
            priority = min(priority, p)
    if priority == 99:
        priority = 5
    if priority == 1:
        return {"priority": priority, "reasoning": f"{poc_title} is the ideal decision-maker. No escalation needed.", "suggestions": []}
    elif priority <= 3:
        return {"priority": priority, "reasoning": f"{poc_title} has influence but may need Founder/CEO sign-off for new partnerships.",
                "suggestions": [
                    {"title": "Founder / Co-Founder", "why": "Final authority on revenue partnerships", "search": f'"{brand}" founder site:linkedin.com'},
                    {"title": "Head of Ecommerce / Operations", "why": "Owns the post-purchase stack", "search": f'"{brand}" head ecommerce site:linkedin.com'},
                ]}
    return {"priority": priority, "reasoning": f"{poc_title or 'This contact'} is unlikely the final decision-maker. Find Founder or Head of Ops.",
            "suggestions": [
                {"title": "Founder / Co-Founder", "why": "Final call on new tech partnerships", "search": f'"{brand}" founder site:linkedin.com'},
                {"title": "Head of Ecommerce / Operations", "why": "Manages post-purchase stack directly", "search": f'"{brand}" head ecommerce operations site:linkedin.com'},
                {"title": "VP / Head of Growth", "why": "Revenue-minded - GMV angle resonates", "search": f'"{brand}" VP growth site:linkedin.com'},
            ]}


# ── Multi-brand / multi-person workflow ──────────────────────────
def run_pipeline_for_brand(url: str, brand: str, poc_name: str, poc_title: str, poc_linkedin: str, poc_email: str) -> dict:
    """Run all 4 agents for a single brand + single person."""
    protection = scan_protection_apps(url)
    metrics = estimate_metrics(url, brand)
    uplift = calculate_revenue_uplift(metrics)
    copy_a = get_copy(brand, poc_name, poc_title, protection, metrics, "A")
    copy_b = get_copy(brand, poc_name, poc_title, protection, metrics, "B")
    copy_c = get_uplift_copy(brand, poc_name, uplift)
    contact = get_contact_suggestion(poc_title, brand)
    return {
        "timestamp": datetime.now().isoformat(),
        "brand": brand, "url": url,
        "poc": {"name": poc_name, "title": poc_title, "linkedin": poc_linkedin, "email": poc_email},
        "protection": protection, "metrics": metrics, "uplift": uplift,
        "copy_a": copy_a, "copy_b": copy_b, "copy_c": copy_c, "contact": contact,
    }


def run_multi_brand_single_person(url_brand_pairs: list, poc_name: str, poc_title: str, poc_linkedin: str, poc_email: str, progress_cb=None) -> list:
    """
    Feature 4: One person managing multiple brands.
    Runs full pipeline per brand, reuses POC info.
    """
    results = []
    for i, (url, brand) in enumerate(url_brand_pairs):
        if progress_cb:
            progress_cb(i, len(url_brand_pairs), brand)
        r = run_pipeline_for_brand(url, brand, poc_name, poc_title, poc_linkedin, poc_email)
        results.append(r)
        time.sleep(0.3)
    return results


def run_multi_person_single_brand(url: str, brand: str, poc_list: list, progress_cb=None) -> list:
    """
    Feature 5: Multiple people from same company.
    Scans brand once, generates person-specific copy per POC.
    """
    # Scan brand ONCE to save time/requests
    protection = scan_protection_apps(url)
    metrics = estimate_metrics(url, brand)
    uplift = calculate_revenue_uplift(metrics)

    results = []
    for i, poc in enumerate(poc_list):
        if progress_cb:
            progress_cb(i, len(poc_list), poc.get("name", f"Person {i+1}"))
        poc_name = poc.get("name", "")
        poc_title = poc.get("title", "")
        copy_a = get_copy(brand, poc_name, poc_title, protection, metrics, "A")
        copy_b = get_copy(brand, poc_name, poc_title, protection, metrics, "B")
        copy_c = get_uplift_copy(brand, poc_name, uplift)
        contact = get_contact_suggestion(poc_title, brand)
        results.append({
            "timestamp": datetime.now().isoformat(),
            "brand": brand, "url": url,
            "poc": {"name": poc_name, "title": poc_title, "linkedin": poc.get("linkedin", ""), "email": poc.get("email", "")},
            "protection": protection, "metrics": metrics, "uplift": uplift,
            "copy_a": copy_a, "copy_b": copy_b, "copy_c": copy_c, "contact": contact,
        })
    return results


# ════════════════════════════════════════════════════════════════
#  RENDER HELPERS
# ════════════════════════════════════════════════════════════════

def initials(name):
    if not name:
        return "??"
    parts = name.strip().split()
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


def render_pipeline(step):
    steps = [("1", "Protection scan", "Route, Navidium…"), ("2", "Metrics + uplift", "AOV + revenue model"),
             ("3", "Outreach copy", "LinkedIn + email A/B/C"), ("4", "Contact quality", "POC assessment")]
    html = '<div class="pipeline-bar">'
    for i, (num, label, sub) in enumerate(steps, 1):
        cls = "active" if i == step else ("done" if i < step else "")
        icon = "✓" if cls == "done" else num
        html += f'<div class="pipe-step"><div class="pipe-num {cls}">{icon}</div><div class="pipe-label"><strong>{label}</strong>{sub}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_result(r, key_suffix=""):
    brand = r["brand"]
    protection = r["protection"]
    metrics = r["metrics"]
    uplift = r.get("uplift", {})
    copy_a = r["copy_a"]
    copy_b = r["copy_b"]
    copy_c = r.get("copy_c")
    contact = r["contact"]
    poc = r["poc"]

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {brand}")
        st.caption(f"{r['url']}  ·  POC: {poc['name'] or 'N/A'} ({poc['title'] or 'N/A'})")
    with col2:
        if metrics["platform"] != "Unknown":
            st.markdown(f'<span class="badge-platform">{metrics["platform"]}</span>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📦 Protection scan", "📊 Metrics + Revenue uplift", "✉ Outreach copy", "👤 Contact quality"])

    with tab1:
        if protection.get("error"):
            st.warning(f"Could not scan site: {protection['error']}")
        elif protection["found"]:
            for app in protection["found"]:
                st.markdown(f'<span class="badge-detected">⚠ {app["app"]} — {app["count"]} signal{"s" if app["count"] > 1 else ""}</span>', unsafe_allow_html=True)
            st.info("Competitor-aware copy is pre-selected. Acknowledge their setup and differentiate on zero-ops + Hartford backing.", icon="💡")
        else:
            st.markdown('<span class="badge-clear">✓ No protection app detected</span>', unsafe_allow_html=True)
            st.success("Strong Parcelis opportunity. Use the margin-leak angle in outreach.", icon="🎯")

    with tab2:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-box"><div class="label">Est. AOV</div><div class="value">{metrics.get("aov_estimate") or "N/A"}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-box"><div class="label">Annual orders</div><div class="value small">{metrics.get("annual_order_estimate") or "N/A"}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-box"><div class="label">Revenue tier</div><div class="value small">{metrics.get("revenue_tier") or "N/A"}</div></div>', unsafe_allow_html=True)

        if metrics.get("signals"):
            with st.expander("Signals used"):
                for s in metrics["signals"]:
                    st.caption(f"• {s}")

        st.markdown("---")
        st.markdown("#### Revenue uplift model")
        st.caption("Assumes 5% buyer charge · Parcelis tiered pricing · Conservative order volume")

        if not uplift or uplift.get("aov") is None:
            st.warning("AOV data insufficient. Run live scanner for price data.")
        elif not uplift.get("viable"):
            st.warning(f"⚠ {uplift.get('reason', 'Not viable at this AOV.')}")
        else:
            u = uplift
            col_u1, col_u2, col_u3, col_u4 = st.columns(4)
            col_u1.markdown(f'<div class="metric-box"><div class="label">Buyer charge/order</div><div class="value">${u["buyer_charge"]:.2f}</div></div>', unsafe_allow_html=True)
            col_u2.markdown(f'<div class="metric-box"><div class="label">Parcelis cost/order</div><div class="value">${u["parcelis_cost"]:.2f}</div></div>', unsafe_allow_html=True)
            col_u3.markdown(f'<div class="metric-box"><div class="label">Net/order</div><div class="value" style="color:#28a745;">${u["net_per_order"]:.2f}</div></div>', unsafe_allow_html=True)
            col_u4.markdown(f'<div class="metric-box"><div class="label">% GMV lift</div><div class="value" style="color:#0056D2;">{u["pct_lift_display"]}</div></div>', unsafe_allow_html=True)
            if u.get("annual_uplift_formatted") and u.get("annual_orders_used"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.success(f"At **{u['annual_orders_used']:,} orders/yr**: **{u['annual_uplift_formatted']}** in net annual revenue — a **{u['pct_lift_display']}** lift on GMV. Tier: {u['tier_label']}.", icon="📈")
            with st.expander("Show tier math"):
                st.markdown(f"""
**Tier:** AOV ~${u['aov']:.0f} → **{u['tier_label']}** (${u['parcelis_cost']:.2f}/order)
- Buyer charge (5% of AOV): **${u['buyer_charge']:.2f}**
- Parcelis cost: **${u['parcelis_cost']:.2f}**
- Net per protected order: **${u['net_per_order']:.2f}** ({u['pct_lift_display']} of GMV)
""")

    with tab3:
        variant_options = ["A — insight-led", "B — outcome-led"]
        if copy_c:
            variant_options.append("C — revenue uplift (live numbers)")
        variant = st.radio("Variant", variant_options, horizontal=True, key=f"var_{brand}_{key_suffix}")
        if variant.startswith("A"):
            v_key, copy = "A", copy_a
        elif variant.startswith("B"):
            v_key, copy = "B", copy_b
        else:
            v_key, copy = "C", copy_c
        if v_key == "C":
            u = uplift
            st.info(f"Revenue uplift variant — **${u['net_per_order']:.2f}/order net**, **{u['pct_lift_display']} GMV lift**" + (f", **{u['annual_uplift_formatted']}/yr**" if u.get('annual_uplift_formatted') else ""), icon="📈")
        else:
            scenario_label = "Competitor-aware" if copy["scenario"] == "has_competitor" else "No-protection"
            st.caption(f"Scenario: **{scenario_label}** · Variant **{v_key}**")
        st.markdown("**LinkedIn DM**")
        dm_val = copy["dm"] if copy else ""
        st.text_area("", value=dm_val, height=110, key=f"li_{brand}_{v_key}_{key_suffix}", label_visibility="collapsed")
        if v_key == "C":
            c = len(dm_val)
            st.caption(f"{'🟢' if c <= 300 else '🔴'} {c}/300 chars")
        st.markdown("**Email subject**")
        st.text_input("", value=copy.get("subject", ""), key=f"sub_{brand}_{v_key}_{key_suffix}", label_visibility="collapsed")
        st.markdown("**Email body**")
        st.text_area("", value=copy.get("body", ""), height=220, key=f"body_{brand}_{v_key}_{key_suffix}", label_visibility="collapsed")

    with tab4:
        stars = "★" * max(1, 6 - contact["priority"]) + "☆" * min(4, contact["priority"] - 1)
        ini = initials(poc["name"])
        st.markdown(f'<div class="contact-row"><div class="contact-avatar">{ini}</div><div><div class="contact-name">{poc["name"] or "Unknown"}</div><div class="contact-title">{poc["title"] or "Unknown title"}</div><div style="color:#0056D2;font-size:0.9rem;margin:4px 0;">{stars}</div><div class="contact-reason">{contact["reasoning"]}</div></div></div>', unsafe_allow_html=True)
        if poc.get("linkedin"):
            st.link_button("Open LinkedIn profile ↗", poc["linkedin"])
        if contact["suggestions"]:
            st.markdown("**Better contacts to find:**")
            for s in contact["suggestions"]:
                st.markdown(f'<div class="suggest-row"><div style="font-size:1.2rem;">🔍</div><div><div class="suggest-title">{s["title"]}</div><div class="suggest-why">{s["why"]}</div><div class="suggest-search">{s["search"]}</div></div></div>', unsafe_allow_html=True)
                st.link_button(f"Search for {s['title'].split('/')[0].strip()} ↗", f"https://www.google.com/search?q={requests.utils.quote(s['search'])}", use_container_width=True)


def results_to_csv(results):
    rows = []
    for r in results:
        u = r.get("uplift") or {}
        cc = r.get("copy_c") or {}
        rows.append({
            "brand": r["brand"], "url": r["url"],
            "poc_name": r["poc"]["name"], "poc_title": r["poc"]["title"],
            "poc_linkedin": r["poc"]["linkedin"], "poc_email": r["poc"]["email"],
            "platform": r["metrics"]["platform"],
            "protection_detected": ", ".join(a["app"] for a in r["protection"].get("found", [])),
            "aov_estimate": r["metrics"].get("aov_estimate"),
            "volume_tier": r["metrics"].get("volume_tier"),
            "annual_order_estimate": r["metrics"].get("annual_order_estimate"),
            "revenue_tier": r["metrics"].get("revenue_tier"),
            "uplift_viable": u.get("viable", False),
            "uplift_net_per_order": "${:.2f}".format(u["net_per_order"]) if u.get("net_per_order") else "",
            "uplift_pct_gmv_lift": u.get("pct_lift_display", ""),
            "uplift_annual_revenue": u.get("annual_uplift_formatted", ""),
            "uplift_tier": u.get("tier_label", ""),
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
        w = csv.DictWriter(buf, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════
#  SESSION STATE INIT
# ════════════════════════════════════════════════════════════════

def init_state():
    if "url_rows" not in st.session_state:
        st.session_state.url_rows = [{"url": "", "brand": ""}]
    if "poc_rows" not in st.session_state:
        st.session_state.poc_rows = [{"name": "", "title": "", "linkedin": "", "email": ""}]
    if "dm_suggestions" not in st.session_state:
        st.session_state.dm_suggestions = {}

init_state()


# ════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown('<div class="sidebar-brand"><h2>📦 Parcelis Scanner</h2><p>Outreach intelligence pipeline v2</p></div>', unsafe_allow_html=True)
    mode = st.radio("Mode", ["Single / Multi lead", "CSV batch"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Protection apps scanned:**")
    for app in PROTECTION_APPS:
        st.caption(f"• {app}")
    st.markdown("---")
    st.markdown("**Revenue uplift tiers:**")
    st.caption("• AOV $0-$200 → $2.50/order")
    st.caption("• AOV $200-$400 → $4.00/order")
    st.caption("• AOV $400-$600 → $5.50/order")
    st.caption("• +$1.50 per $200 band above")
    st.markdown("---")
    st.caption("Sandeep Trivedi · VP Partnerships  \n[myparcelis.com](https://myparcelis.com)")


# ════════════════════════════════════════════════════════════════
#  MAIN PAGE
# ════════════════════════════════════════════════════════════════

st.markdown("""
<div class="parcelis-header">
    <div>
        <h1>Parcelis Outreach Scanner</h1>
        <p>Scan → Research → Revenue uplift → Draft A/B/C → Suggest</p>
    </div>
    <span class="header-badge">v2.1</span>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  SINGLE / MULTI LEAD MODE
# ════════════════════════════════════════════════════════════════

if mode == "Single / Multi lead":

    # ── STEP 1: Brand website(s) ─────────────────────────────────
    st.markdown("### Step 1 — Brand website(s)")
    st.caption("Add one URL per brand. For a person managing multiple brands, add each brand separately.")

    for i, row in enumerate(st.session_state.url_rows):
        col_url, col_brand, col_detect, col_remove = st.columns([3, 2, 1, 0.5])
        with col_url:
            new_url = st.text_input(
                f"URL {i + 1}", value=row["url"],
                placeholder="https://brand.com", key=f"url_{i}",
                label_visibility="collapsed" if i > 0 else "visible",
            )
            st.session_state.url_rows[i]["url"] = new_url
        with col_brand:
            new_brand = st.text_input(
                f"Brand {i + 1}", value=row["brand"],
                placeholder="Brand name (auto-detect →)", key=f"brand_{i}",
                label_visibility="collapsed" if i > 0 else "visible",
            )
            st.session_state.url_rows[i]["brand"] = new_brand
        with col_detect:
            if i == 0:
                st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Auto-detect", key=f"detect_{i}", help="Scrape brand name from website"):
                url_val = st.session_state.url_rows[i]["url"].strip()
                if url_val:
                    if not url_val.startswith("http"):
                        url_val = "https://" + url_val
                    with st.spinner("Detecting..."):
                        detected = extract_brand_name(url_val)
                    st.session_state.url_rows[i]["brand"] = detected
                    st.rerun()
        with col_remove:
            if i == 0:
                st.markdown("<br>", unsafe_allow_html=True)
            if i > 0 and st.button("✕", key=f"rm_url_{i}", help="Remove this URL"):
                st.session_state.url_rows.pop(i)
                st.rerun()

    col_add_url, _ = st.columns([2, 5])
    with col_add_url:
        if st.button("+ Add another brand URL", help="Feature 4: one person, multiple brands"):
            st.session_state.url_rows.append({"url": "", "brand": ""})
            st.rerun()

    st.markdown("---")

    # ── STEP 2: Contact(s) ────────────────────────────────────────
    st.markdown("### Step 2 — Contact(s)")
    st.caption("Add one or more contacts. For multiple people at the same company, the brand scan runs once.")

    for i, poc in enumerate(st.session_state.poc_rows):
        label = poc["name"] or f"Person {i + 1}"
        with st.expander(f"{'👤' if i == 0 else '👤'} {label}", expanded=(i == 0)):

            col_name, col_title = st.columns(2)
            with col_name:
                poc["name"] = st.text_input("Full name", value=poc["name"], placeholder="Jane Smith", key=f"poc_name_{i}")
            with col_title:
                poc["title"] = st.text_input("Job title", value=poc["title"], placeholder="Co-Founder", key=f"poc_title_{i}")

            col_li, col_email = st.columns(2)
            with col_li:
                poc["linkedin"] = st.text_input("LinkedIn URL", value=poc["linkedin"], placeholder="https://linkedin.com/in/...", key=f"poc_li_{i}")
            with col_email:
                poc["email"] = st.text_input("Email", value=poc["email"], placeholder="jane@brand.com", key=f"poc_email_{i}")

            btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1.5, 3])
            with btn_col1:
                # Feature 3: Fetch from LinkedIn
                if st.button("🔍 Fetch from LinkedIn", key=f"fetch_li_{i}", help="Extract name + title from public LinkedIn profile"):
                    li_url = poc["linkedin"].strip()
                    if li_url:
                        with st.spinner("Fetching LinkedIn profile..."):
                            info = extract_linkedin_info(li_url)
                        if info.get("error"):
                            st.warning(f"Could not fetch profile: {info['error']}")
                        else:
                            if info["name"] and not poc["name"]:
                                st.session_state.poc_rows[i]["name"] = info["name"]
                            if info["title"] and not poc["title"]:
                                st.session_state.poc_rows[i]["title"] = info["title"]
                            if info["email"] and not poc["email"]:
                                st.session_state.poc_rows[i]["email"] = info["email"]
                            st.success(f"Fetched: {info['name']} — {info['title'][:50]}")
                            st.rerun()
                    else:
                        st.warning("Enter a LinkedIn URL first")

            with btn_col2:
                # Feature 2: Suggest decision makers
                primary_brand = st.session_state.url_rows[0]["brand"].strip() or "this brand"
                if st.button("💡 Find decision maker", key=f"find_dm_{i}", help="Google search for Founder/CEO on LinkedIn"):
                    with st.spinner(f"Searching LinkedIn for {primary_brand} decision makers..."):
                        suggestions = find_decision_makers(primary_brand)
                    st.session_state.dm_suggestions[i] = suggestions
                    st.rerun()

            with btn_col3:
                if i > 0 and st.button(f"Remove person {i + 1}", key=f"rm_poc_{i}"):
                    st.session_state.poc_rows.pop(i)
                    if i in st.session_state.dm_suggestions:
                        del st.session_state.dm_suggestions[i]
                    st.rerun()

            # Show DM suggestions inline
            if i in st.session_state.dm_suggestions:
                sug = st.session_state.dm_suggestions[i]
                if sug:
                    st.markdown("**Suggested decision makers:**")
                    for dm in sug:
                        col_dm1, col_dm2 = st.columns([3, 1])
                        with col_dm1:
                            st.markdown(f'<div class="dm-suggestion"><div class="dm-name">{dm["name"]}</div><div class="dm-title">{dm["title"] or "Title not available"}</div></div>', unsafe_allow_html=True)
                        with col_dm2:
                            if st.button("Use this", key=f"use_dm_{i}_{dm['name'][:10]}"):
                                st.session_state.poc_rows[i]["name"] = dm["name"]
                                st.session_state.poc_rows[i]["title"] = dm["title"]
                                st.session_state.poc_rows[i]["linkedin"] = dm["linkedin_url"]
                                del st.session_state.dm_suggestions[i]
                                st.rerun()
                else:
                    st.info("No LinkedIn results found. Try a more specific brand name.")

        st.session_state.poc_rows[i] = poc

    col_add_poc, _ = st.columns([2, 5])
    with col_add_poc:
        if st.button("+ Add another person", help="Feature 5: multiple contacts from same company"):
            st.session_state.poc_rows.append({"name": "", "title": "", "linkedin": "", "email": ""})
            st.rerun()

    st.markdown("---")

    # ── RUN BUTTON ────────────────────────────────────────────────
    run_label = "▶ Run workflow"
    n_urls = len([r for r in st.session_state.url_rows if r["url"].strip()])
    n_pocs = len([p for p in st.session_state.poc_rows if p["name"].strip() or p["linkedin"].strip()])
    if n_urls > 1 and n_pocs > 1:
        run_label = f"▶ Run multi-brand + multi-person ({n_urls} brands × {n_pocs} contacts)"
    elif n_urls > 1:
        run_label = f"▶ Run multi-brand workflow ({n_urls} brands, {n_pocs or 1} contact)"
    elif n_pocs > 1:
        run_label = f"▶ Run multi-person workflow ({n_urls} brand, {n_pocs} contacts)"

    run_clicked = st.button(run_label, type="primary", use_container_width=True)

    if run_clicked:
        # Collect and validate inputs
        url_brand_pairs = []
        for row in st.session_state.url_rows:
            u = row["url"].strip()
            b = row["brand"].strip()
            if u:
                if not u.startswith("http"):
                    u = "https://" + u
                if not b:
                    b = urlparse(u).netloc.replace("www.", "").split(".")[0].title()
                url_brand_pairs.append((u, b))

        poc_list = [
            p for p in st.session_state.poc_rows
            if p.get("name", "").strip() or p.get("linkedin", "").strip()
        ]
        if not poc_list:
            poc_list = [{"name": "", "title": "", "linkedin": "", "email": ""}]

        if not url_brand_pairs:
            st.warning("Please enter at least one store URL.")
        else:
            pipeline_ph = st.empty()
            prog = st.progress(0)
            status = st.empty()

            all_results = []
            total_jobs = len(url_brand_pairs) * len(poc_list)
            job = 0
            job_slice = 90 / max(total_jobs, 1)

            for url, brand in url_brand_pairs:
                for poc in poc_list:
                    job += 1
                    pct_base = ((job - 1) / total_jobs) * 90

                    with pipeline_ph:
                        render_pipeline(1)
                    prog.progress(min(int(pct_base + job_slice * 0.10), 99))
                    status.info(f"[{job}/{total_jobs}] Scanning {brand} for {poc.get('name') or 'contact'}...")

                    with pipeline_ph:
                        render_pipeline(2)
                    prog.progress(min(int(pct_base + job_slice * 0.30), 99))

                    with pipeline_ph:
                        render_pipeline(3)
                    prog.progress(min(int(pct_base + job_slice * 0.65), 99))

                    with pipeline_ph:
                        render_pipeline(4)
                    prog.progress(min(int(pct_base + job_slice * 0.90), 99))

                    result = run_pipeline_for_brand(
                        url, brand,
                        poc.get("name", ""), poc.get("title", ""),
                        poc.get("linkedin", ""), poc.get("email", "")
                    )
                    all_results.append(result)
                    time.sleep(0.2)

            prog.progress(100)
            status.success(f"Complete — {len(all_results)} result{'s' if len(all_results) > 1 else ''} ready.")
            pipeline_ph.empty()
            time.sleep(0.3)

            st.markdown("---")
            st.markdown(f"### Results ({len(all_results)})")

            if len(all_results) == 1:
                render_result(all_results[0])
            else:
                tab_labels = [f"{r['brand']} — {r['poc']['name'] or 'N/A'}" for r in all_results]
                result_tabs = st.tabs(tab_labels)
                for tab, result in zip(result_tabs, all_results):
                    with tab:
                        render_result(result, key_suffix=f"{result['brand']}_{result['poc']['name']}")

            csv_data = results_to_csv(all_results)
            st.download_button(
                "⬇ Download results CSV",
                data=csv_data,
                file_name=f"parcelis_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )


# ════════════════════════════════════════════════════════════════
#  CSV BATCH MODE
# ════════════════════════════════════════════════════════════════

else:
    st.markdown("#### Upload your leads CSV")
    st.caption("Required: `url`, `brand_name`, `poc_name`, `poc_title`  ·  Optional: `poc_linkedin`, `poc_email`")

    sample_csv = "url,brand_name,poc_name,poc_title,poc_linkedin,poc_email\nhttps://www.beardbrand.com,Beardbrand,Eric Bandholz,Founder,https://linkedin.com/in/ericbandholz,eric@beardbrand.com\nhttps://www.huckberry.com,Huckberry,Richard Greiner,Co-Founder,,\nhttps://www.chubbiesshorts.com,Chubbies,Tom Montgomery,Co-Founder,,\n"
    st.download_button("⬇ Download sample CSV template", data=sample_csv, file_name="parcelis_leads_template.csv", mime="text/csv")

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

        if st.button("▶ Run batch pipeline", type="primary", use_container_width=True):
            results = []
            pipeline_ph = st.empty()
            prog = st.progress(0)
            status = st.empty()

            row_slice = 90 / max(len(rows), 1)
            for i, row in enumerate(rows):
                brand = row.get("brand_name") or urlparse(row.get("url", "")).netloc.replace("www.", "").split(".")[0].title()
                status.info(f"Processing {i + 1}/{len(rows)}: **{brand}**")
                step_base = (i / len(rows)) * 90

                with pipeline_ph: render_pipeline(1)
                prog.progress(min(int(step_base + row_slice * 0.10), 99))
                protection = scan_protection_apps(row.get("url", ""))

                with pipeline_ph: render_pipeline(2)
                prog.progress(min(int(step_base + row_slice * 0.35), 99))
                metrics = estimate_metrics(row.get("url", ""), brand)
                uplift = calculate_revenue_uplift(metrics)

                with pipeline_ph: render_pipeline(3)
                prog.progress(min(int(step_base + row_slice * 0.65), 99))
                copy_a = get_copy(brand, row.get("poc_name", ""), row.get("poc_title", ""), protection, metrics, "A")
                copy_b = get_copy(brand, row.get("poc_name", ""), row.get("poc_title", ""), protection, metrics, "B")
                copy_c = get_uplift_copy(brand, row.get("poc_name", ""), uplift)

                with pipeline_ph: render_pipeline(4)
                prog.progress(min(int(step_base + row_slice * 0.90), 99))
                contact = get_contact_suggestion(row.get("poc_title", ""), brand)

                results.append({
                    "timestamp": datetime.now().isoformat(), "brand": brand, "url": row.get("url", ""),
                    "poc": {"name": row.get("poc_name", ""), "title": row.get("poc_title", ""),
                            "linkedin": row.get("poc_linkedin", ""), "email": row.get("poc_email", "")},
                    "protection": protection, "metrics": metrics, "uplift": uplift,
                    "copy_a": copy_a, "copy_b": copy_b, "copy_c": copy_c, "contact": contact,
                })
                time.sleep(0.4)

            prog.progress(100)
            status.success(f"Batch complete — {len(results)} leads processed.")
            pipeline_ph.empty()
            time.sleep(0.4)

            no_protection = [r for r in results if not r["protection"]["found"]]
            viable_uplift = [r for r in results if r.get("uplift", {}).get("viable")]
            ideal_contacts = [r for r in results if r["contact"]["priority"] == 1]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total leads", len(results))
            m2.metric("Unprotected", len(no_protection))
            m3.metric("Uplift viable", len(viable_uplift))
            m4.metric("Ideal contact", len(ideal_contacts))

            viable = [(r, r["uplift"]) for r in results if r.get("uplift", {}).get("annual_uplift")]
            if viable:
                viable.sort(key=lambda x: x[1]["annual_uplift"], reverse=True)
                st.markdown("#### Top revenue uplift opportunities")
                for rank, (r, u) in enumerate(viable[:3], 1):
                    st.markdown(f"**{rank}. {r['brand']}** — {u['annual_uplift_formatted']}/yr · {u['pct_lift_display']} GMV lift")

            st.markdown("### Results")
            result_tabs = st.tabs([r["brand"] for r in results])
            for tab, result in zip(result_tabs, results):
                with tab:
                    render_result(result, key_suffix=result["brand"])

            csv_out = results_to_csv(results)
            st.download_button("⬇ Download full results CSV", data=csv_out,
                               file_name=f"parcelis_batch_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                               mime="text/csv", use_container_width=True)
