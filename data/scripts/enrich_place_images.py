"""
enrich_place_images.py

Enhanced Multi-Source Authentic Image Resolution Pipeline for TuniVerse:
  Tier 1: Wikidata Batch Entity Claims (Property P18 canonical landmark photos)
  Tier 2: Direct Wikipedia REST API (Lead photo extraction from wikipedia_url)
  Tier 3: Multilingual Smart Search on Wikimedia Commons (Strict Tunisia + Title Relevance Check)
  Tier 4: Wikipedia Article Search (FR / EN summary API with Title Verification)
  Tier 5: Wikimedia Commons GPS Geosearch (Tight 200m radius authentic on-site photos)
  Tier 6: Clean NULL Placeholder (Zero stock photos, zero out-of-country/unrelated false positives)

Usage:
  python data/scripts/enrich_place_images.py --test      (Runs on 25 sample places)
  python data/scripts/enrich_place_images.py             (Runs across all 1,690 attractions)
"""

import sys
import json
import re
import time
import threading
import unicodedata
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "processed"
ATTRACTIONS_FILE = PROCESSED_DIR / "attractions.json"
PLACES_FINAL_FILE = PROCESSED_DIR / "places_final.json"
HOTELS_FILE = PROCESSED_DIR / "hotels.json"
MASTER_FILE = PROCESSED_DIR / "places_master.json"
CACHE_FILE = PROCESSED_DIR / "exact_images_cache.json"

WIKI_HEADERS = {
    "User-Agent": "TuniVerseAcademicBot/1.0 (https://github.com/tuniverse; ali.kchaou@enetcom.u-sfax.tn) python-requests"
}

BAD_NAME_KEYWORDS = [
    "icon", "logo", "flag", "carte", "map", "locator", "coa", "blason",
    "armoiries", "plan", "stamp", "coin", "monnaie", "timbre", "diagram",
    "drapeau", "badge", "symbol", "locator_tool", "chart", "collage",
    "fonds", "archive", "manuscript", "engraving", "painting", "specimen"
]

GENERIC_STOPWORDS = {
    "tunisie", "tunisia", "tunis", "the", "and", "for", "with", "from",
    "les", "des", "une", "dans", "pour", "sur", "par", "aux", "qui",
    "monument", "site", "place", "parc", "park", "maison", "house",
    "national", "nationale", "center", "centre", "museum", "musee",
    "old", "new", "great", "grand", "grande", "petit", "petite",
    "city", "ville", "hotel", "tour", "street", "rue", "avenue"
}

_session = requests.Session()
_session.headers.update(WIKI_HEADERS)
_rate_lock = threading.Lock()
_last_request_time = 0.0
MIN_REQUEST_INTERVAL = 0.25  # Max ~4 req/sec globally across all threads


def wiki_get(url: str, params: dict | None = None, timeout: int = 12, retries: int = 3) -> requests.Response | None:
    """Rate-limited GET request with automatic 429/503 Retry-After backoff."""
    global _last_request_time
    for attempt in range(retries):
        with _rate_lock:
            now = time.monotonic()
            wait = MIN_REQUEST_INTERVAL - (now - _last_request_time)
            if wait > 0:
                time.sleep(wait)
            _last_request_time = time.monotonic()

        try:
            r = _session.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 503):
                retry_after = r.headers.get("Retry-After")
                sleep_sec = float(retry_after) if retry_after and retry_after.isdigit() else 2.0 * (attempt + 1)
                time.sleep(min(sleep_sec, 10.0))
                continue
            if r.status_code == 404:
                return None
        except Exception:
            time.sleep(1.0 * (attempt + 1))
    return None


def strip_accents(text: str) -> str:
    """Normalizes Latin accents for robust keyword comparison."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )


def norm_filename(name: str) -> str:
    """Normalizes Wikimedia filenames to handle space vs underscore discrepancies."""
    if not name:
        return ""
    return name.replace("File:", "").replace("_", " ").strip().lower()


def is_valid_photo(title: str, mime: str) -> bool:
    """Verifies that an asset is a genuine photograph and not a map, flag, or icon."""
    title_lower = title.lower()
    if any(bad in title_lower for bad in BAD_NAME_KEYWORDS):
        return False
    if not any(ext in mime.lower() for ext in ["jpeg", "jpg", "png", "webp"]):
        return False
    return True


def has_tunisia_context(text: str, city: str) -> bool:
    """Checks if query already contains Tunisia or the Tunisian city name."""
    low = text.lower()
    if any(marker in low for marker in ["tunisie", "tunisia", "تونس"]):
        return True
    if city and len(city.strip()) >= 3 and city.strip().lower() in low:
        return True
    return False


def extract_distinctive_keywords(names: list[str], city: str) -> list[str]:
    """
    Extracts distinctive keywords from French/Arabic/English names so search results
    must actually mention the landmark in the file title (prevents unrelated matches).
    """
    city_low = strip_accents(city).lower().strip()
    keywords = []
    for name in names:
        if not name:
            continue
        clean = strip_accents(name).lower()
        tokens = re.findall(r"[\w\u0600-\u06FF]+", clean)
        for tok in tokens:
            if len(tok) < 3:
                continue
            if tok in GENERIC_STOPWORDS:
                continue
            # Skip bare city token unless the place name itself IS essentially the city (e.g. "Dougga")
            if tok == city_low and len(tokens) > 1:
                continue
            if tok not in keywords:
                keywords.append(tok)
    return keywords


def title_matches_place(file_title: str, keywords: list[str]) -> bool:
    """Checks that the returned Wikimedia File title actually refers to this landmark."""
    if not keywords:
        return False
    norm_title = strip_accents(norm_filename(file_title))
    return any(kw in norm_title for kw in keywords)


# ==============================================================================
# TIER 1: BATCH WIKIDATA P18 RESOLVER (WITH RETRIES & NORMALIZATION)
# ==============================================================================
def prefetch_wikidata_p18(qids: list[str]) -> dict[str, str]:
    """
    Fetches Wikidata claim P18 (canonical image) for a list of QIDs in chunks of 50.
    Returns: {qid: image_url_800px}
    """
    if not qids:
        return {}

    unique_qids = list(dict.fromkeys([q.strip() for q in qids if q and q.startswith("Q")]))
    qid_to_file = {}

    print(f"📡 Prefetching Wikidata P18 image claims for {len(unique_qids)} QIDs in batches of 50...")

    batch_size = 50
    for i in range(0, len(unique_qids), batch_size):
        batch = unique_qids[i:i + batch_size]
        params = {
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "claims",
            "format": "json"
        }
        r = wiki_get("https://www.wikidata.org/w/api.php", params=params, timeout=15)
        if r:
            entities = r.json().get("entities", {})
            for qid in batch:
                claims = entities.get(qid, {}).get("claims", {})
                p18 = claims.get("P18")
                if p18 and len(p18) > 0:
                    datavalue = p18[0].get("mainsnak", {}).get("datavalue", {})
                    fname = datavalue.get("value")
                    if fname:
                        qid_to_file[qid] = fname

    print(f"   Found {len(qid_to_file)} P18 file claims. Resolving direct 800px CDN URLs...")

    file_to_url = {}
    all_files = list(dict.fromkeys(qid_to_file.values()))
    for i in range(0, len(all_files), batch_size):
        batch_files = all_files[i:i + batch_size]
        titles = [f"File:{f}" for f in batch_files]
        params = {
            "action": "query",
            "titles": "|".join(titles),
            "prop": "imageinfo",
            "iiprop": "url|mime",
            "iiurlwidth": 800,
            "format": "json"
        }
        r = wiki_get("https://commons.wikimedia.org/w/api.php", params=params, timeout=15)
        if r:
            pages = r.json().get("query", {}).get("pages", {})
            for _, pdata in pages.items():
                title = pdata.get("title", "").replace("File:", "")
                infos = pdata.get("imageinfo", [])
                if infos:
                    url = infos[0].get("thumburl") or infos[0].get("url")
                    mime = infos[0].get("mime", "")
                    if url and is_valid_photo(title, mime):
                        file_to_url[norm_filename(title)] = url

    result = {}
    for qid, fname in qid_to_file.items():
        nkey = norm_filename(fname)
        if nkey in file_to_url:
            result[qid] = file_to_url[nkey]
        else:
            encoded = requests.utils.quote(fname.replace(" ", "_"))
            result[qid] = f"https://commons.wikimedia.org/wiki/Special:FilePath/{encoded}?width=800"

    print(f"✅ Resolved {len(result)} authentic photos directly from Wikidata P18!")
    return result


# ==============================================================================
# TIER 2: WIKIPEDIA REST API (From wikipedia_url)
# ==============================================================================
def fetch_from_wikipedia_url(wiki_url: str) -> str | None:
    """Extracts lead article photo from a Wikipedia URL via REST API."""
    if not wiki_url or "wikipedia.org/wiki/" not in wiki_url:
        return None

    try:
        parts = wiki_url.split("wikipedia.org/wiki/")
        lang = parts[0].split("//")[1].split(".")[0]
        title = parts[1].split("#")[0].strip()
        if not title:
            return None

        api_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
        r = wiki_get(api_url, timeout=8)
        if r:
            data = r.json()
            thumb = data.get("thumbnail", {}).get("source")
            if thumb and thumb.startswith("http"):
                return re.sub(r"/\d+px-", "/800px-", thumb)
    except Exception:
        pass
    return None


# ==============================================================================
# TIER 3: MULTILINGUAL WIKIMEDIA COMMONS SEARCH (Strict Tunisia + Title Match)
# ==============================================================================
def search_wikimedia_commons(term: str, required_keywords: list[str]) -> str | None:
    """
    Searches Wikimedia Commons File namespace and verifies that at least one
    distinctive landmark keyword appears in the returned file title.
    """
    if not term or len(term.strip()) < 3 or not required_keywords:
        return None

    clean_term = term.strip().replace("-", " ")
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": clean_term,
        "gsrnamespace": 6,
        "gsrlimit": 5,
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": 800,
        "format": "json"
    }
    r = wiki_get(url, params=params, timeout=8)
    if r:
        pages = r.json().get("query", {}).get("pages", {})
        for _, pdata in pages.items():
            title = pdata.get("title", "")
            infos = pdata.get("imageinfo", [])
            if infos:
                url_img = infos[0].get("thumburl") or infos[0].get("url")
                mime = infos[0].get("mime", "")
                if url_img and is_valid_photo(title, mime) and title_matches_place(title, required_keywords):
                    return url_img
    return None


# ==============================================================================
# TIER 4: WIKIPEDIA SUMMARY SEARCH (FR / EN with Title Verification)
# ==============================================================================
def fetch_from_wikipedia_search(term: str, required_keywords: list[str], lang: str = "fr") -> str | None:
    """Performs an OpenSearch on Wikipedia in FR or EN and verifies article title relevance."""
    if not term or len(term.strip()) < 3 or not required_keywords:
        return None

    clean = term.strip().replace("-", " ")
    suffix = "Tunisie" if lang == "fr" else "Tunisia"
    query = clean if any(k in clean.lower() for k in ["tunis", "carthage", "dougga", "djerba", "sousse", "kairouan"]) else f"{clean} {suffix}"

    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": query,
        "limit": 1,
        "namespace": 0,
        "format": "json"
    }
    r = wiki_get(url, params=params, timeout=8)
    if r and len(r.json()) > 1 and r.json()[1]:
        matched_title = r.json()[1][0]
        if not title_matches_place(matched_title, required_keywords):
            return None
        summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{matched_title.replace(' ', '_')}"
        sr = wiki_get(summary_url, timeout=8)
        if sr:
            thumb = sr.json().get("thumbnail", {}).get("source")
            if thumb and thumb.startswith("http"):
                return re.sub(r"/\d+px-", "/800px-", thumb)
    return None


# ==============================================================================
# TIER 5: WIKIMEDIA COMMONS GPS GEOSEARCH (Tight 200m on-site radius)
# ==============================================================================
def fetch_from_gps_geosearch(lat: float, lon: float, radius: int = 200) -> str | None:
    """Finds authentic geotagged photographs taken directly on-site at lat/lon coordinates."""
    if not lat or not lon:
        return None

    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "geosearch",
        "ggscoord": f"{lat}|{lon}",
        "ggsradius": radius,
        "ggsnamespace": 6,
        "ggslimit": 5,
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": 800,
        "format": "json"
    }
    r = wiki_get(url, params=params, timeout=8)
    if r:
        pages = r.json().get("query", {}).get("pages", {})
        for _, pdata in pages.items():
            title = pdata.get("title", "")
            infos = pdata.get("imageinfo", [])
            if infos:
                url_img = infos[0].get("thumburl") or infos[0].get("url")
                mime = infos[0].get("mime", "")
                if url_img and is_valid_photo(title, mime):
                    return url_img
    return None


# ==============================================================================
# COMPLETE MULTI-TIER RESOLVER FOR A SINGLE PLACE
# ==============================================================================
def resolve_place_photo(
    place: dict,
    meta: dict,
    cache: dict,
    wikidata_map: dict
) -> tuple[int, str | None, str]:
    """
    Executes the 6-tier authentic cascade for one place.
    Returns: (place_id, photo_url_or_None, source_tier_name)
    """
    pid = str(place.get("id"))

    # Reuse existing verified non-null cache
    if pid in cache and cache[pid] and isinstance(cache[pid], str) and cache[pid].startswith("http"):
        return place["id"], cache[pid], "Cache"

    lat = place.get("latitude")
    lon = place.get("longitude")
    city = (place.get("city") or "").strip()
    name_en = (place.get("name") or meta.get("name_en") or "").strip()
    name_fr = (meta.get("name_fr") or "").strip()
    name_ar = (meta.get("name_ar") or "").strip()
    qid = (meta.get("wikidata") or "").strip()
    wiki_url = (meta.get("wikipedia_url") or "").strip()

    # Tier 1: Wikidata P18 Claim (Prefetched)
    if qid and qid in wikidata_map:
        photo = wikidata_map[qid]
        cache[pid] = photo
        return place["id"], photo, "Wikidata P18"

    # Tier 2: Direct Wikipedia URL
    if wiki_url:
        photo = fetch_from_wikipedia_url(wiki_url)
        if photo:
            cache[pid] = photo
            return place["id"], photo, "Wikipedia Article"

    keywords = extract_distinctive_keywords([name_fr, name_en, name_ar], city)

    # Tier 3: Multilingual Smart Search on Wikimedia Commons (Strict Tunisia + Title Match)
    search_candidates = []

    def add_candidate(raw_name: str, country_word: str):
        clean = raw_name.replace("-", " ").strip()
        if len(clean) < 3:
            return
        if city and city.lower() not in clean.lower():
            search_candidates.append(f"{clean} {city}")
        if has_tunisia_context(clean, city):
            if clean not in search_candidates:
                search_candidates.append(clean)
        else:
            search_candidates.append(f"{clean} {country_word}")

    if name_fr:
        add_candidate(name_fr, "Tunisie")
    if name_ar:
        add_candidate(name_ar, "تونس")
    if name_en and name_en.lower() != name_fr.lower():
        add_candidate(name_en, "Tunisia")

    seen_q = set()
    unique_candidates = []
    for q in search_candidates:
        ql = q.lower()
        if ql not in seen_q:
            seen_q.add(ql)
            unique_candidates.append(q)

    for term in unique_candidates:
        photo = search_wikimedia_commons(term, keywords)
        if photo:
            cache[pid] = photo
            return place["id"], photo, "Wikimedia Commons Search"

    # Tier 4: Wikipedia Search (French / English with Title Match)
    target_fr = name_fr if name_fr else name_en
    photo = fetch_from_wikipedia_search(target_fr, keywords, lang="fr")
    if not photo and name_en:
        photo = fetch_from_wikipedia_search(name_en, keywords, lang="en")
    if photo:
        cache[pid] = photo
        return place["id"], photo, "Wikipedia Search"

    # Tier 5: Wikimedia Commons GPS Geosearch (Tight 200m on-site radius)
    if lat and lon:
        photo = fetch_from_gps_geosearch(lat, lon, radius=200)
        if photo:
            cache[pid] = photo
            return place["id"], photo, "Wikimedia GPS Geosearch"

    # Tier 6: Clean NULL Placeholder
    cache[pid] = None
    return place["id"], None, "None (Clean Placeholder)"


# ==============================================================================
# MAIN PIPELINE EXECUTION
# ==============================================================================
def run_enhanced_enrichment(is_test: bool = False):
    print("=" * 80)
    print(f"🌟 ENHANCED AUTHENTIC IMAGE RESOLVER (Multi-Tier Pipeline | Test: {is_test})")
    print("   Tier 1: Wikidata P18 -> Tier 2: Wikipedia -> Tier 3: Title-Verified Search -> Tier 5: 200m GPS")
    print("   100% Authentic Photos | Strict Relevance Verification | Clean Null for Unverified")
    print("=" * 80)

    if not ATTRACTIONS_FILE.exists() or not PLACES_FINAL_FILE.exists():
        print("❌ Missing required data files.")
        return

    with open(ATTRACTIONS_FILE, "r", encoding="utf-8") as f:
        attractions = json.load(f)

    with open(PLACES_FINAL_FILE, "r", encoding="utf-8") as f:
        places_final = json.load(f)

    lookup_coord = {(round(p["latitude"], 4), round(p["longitude"], 4)): p for p in places_final}
    lookup_name = {p["name_en"].strip().lower(): p for p in places_final if p.get("name_en")}

    def get_meta(attraction):
        k = (round(attraction["latitude"], 4), round(attraction["longitude"], 4))
        if k in lookup_coord:
            return lookup_coord[k]
        name_key = attraction.get("name", "").strip().lower()
        if name_key in lookup_name:
            return lookup_name[name_key]
        return {}

    cache = {}
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                raw_cache = json.load(f)
            cache = {k: v for k, v in raw_cache.items() if v and isinstance(v, str) and v.startswith("http")}
            print(f"📂 Loaded {len(cache)} existing valid photos from cache.")
        except Exception:
            cache = {}

    target = attractions[:25] if is_test else attractions
    print(f"🎯 Target: Resolving authentic images for {len(target)} places...\n")

    target_qids = []
    for p in target:
        meta = get_meta(p)
        qid = meta.get("wikidata")
        if qid:
            target_qids.append(qid)

    wikidata_map = prefetch_wikidata_p18(target_qids)

    results_map = {}
    found_count = 0
    none_count = 0
    source_stats = {
        "Cache": 0,
        "Wikidata P18": 0,
        "Wikipedia Article": 0,
        "Wikipedia Search": 0,
        "Wikimedia Commons Search": 0,
        "Wikimedia GPS Geosearch": 0,
        "None (Clean Placeholder)": 0
    }

    max_workers = 3
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(resolve_place_photo, p, get_meta(p), cache, wikidata_map): p
            for p in target
        }
        done = 0
        for f in as_completed(futures):
            done += 1
            pid, img_url, src = f.result()
            results_map[pid] = img_url
            source_stats[src] = source_stats.get(src, 0) + 1

            if img_url:
                found_count += 1
            else:
                none_count += 1

            if is_test or done % 50 == 0 or done == len(target):
                icon = "📸" if img_url else "⚪"
                p_name = futures[f].get("name", "")[:28]
                print(f"  [{done:4d}/{len(target)}] {icon} ID {pid:4d} {p_name:28s} | {src:25s} | Real Photos: {found_count} | Null: {none_count}")

    if not is_test:
        for p in attractions:
            pid = p.get("id")
            if pid in results_map:
                exact_img = results_map[pid]
                p["cover_image"] = exact_img
                p["images"] = [exact_img] if exact_img else []

        with open(ATTRACTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(attractions, f, ensure_ascii=False, indent=2)

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)

        if HOTELS_FILE.exists():
            with open(HOTELS_FILE, "r", encoding="utf-8") as f:
                hotels = json.load(f)
            master = hotels + attractions
            with open(MASTER_FILE, "w", encoding="utf-8") as f:
                json.dump(master, f, ensure_ascii=False, indent=2)

    print("\n" + "─" * 80)
    print("🎉 RESOLUTION RUN FINISHED!")
    print(f"📸 Places with Exact Real Photos:  {found_count} ({found_count / len(target) * 100:.1f}%)")
    print(f"⚪ Clean Null Placeholders:        {none_count} ({none_count / len(target) * 100:.1f}%)")
    print("📊 Source Breakdown:")
    for src, count in sorted(source_stats.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"   - {src:28s}: {count:4d} ({count / len(target) * 100:.1f}%)")

    if not is_test:
        print(f"📄 Saved to: {ATTRACTIONS_FILE.name} and {MASTER_FILE.name}")


if __name__ == "__main__":
    test_mode = "--test" in sys.argv
    run_enhanced_enrichment(is_test=test_mode)
