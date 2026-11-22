"""
enrich_place_descriptions.py

Recovers descriptions for Tunisian tourist places by querying French Wikipedia 
(which has extensive coverage of Tunisian monuments/heritage) and translating 
the summary into clean English with rotating academic quotas.

Usage:
  python data/scripts/enrich_place_descriptions.py --test            (Runs test on 3 places)
  python data/scripts/enrich_place_descriptions.py --start el-Mida   (Resumes starting from a place name)
  python data/scripts/enrich_place_descriptions.py --start 764       (Resumes starting from step number)
  python data/scripts/enrich_place_descriptions.py                   (Runs full enrichment across missing places)
"""

import sys
import json
import re
import time
import urllib.parse
from pathlib import Path
import requests
from deep_translator import MyMemoryTranslator

BASE_DIR = Path(__file__).parent.parent
INPUT_FILE = BASE_DIR / "processed" / "places_final.json"
CHECKPOINT_FILE = BASE_DIR / "processed" / "fr_checkpoint.json"

HEADERS = {
    "User-Agent": "TuniVerse/1.0 (academic project ENET'Com; tuniverse-bot)"
}

TRANSLATION_EMAILS = [
    "tuniverse.academic@enetcom.u-sfax.tn",
    "ali.tuniverse@enetcom.tn",
    "racem.tuniverse@enetcom.tn"
]
current_email_idx = 0


def get_fr_summary(title: str) -> str | None:
    """Fetch summary extract from French Wikipedia REST API."""
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            extract = r.json().get("extract", "").strip()
            if len(extract) > 40:
                return extract
    except Exception:
        pass
    return None


def search_fr_wikipedia(name: str) -> str | None:
    """Search French Wikipedia for a place name and return top title if relevant."""
    if not name or len(name) < 3:
        return None

    # Search query scoped to Tunisia
    query = f"{name} Tunisie" if "tunisie" not in name.lower() else name
    url = "https://fr.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 2,
        "format": "json"
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            results = r.json().get("query", {}).get("search", [])
            for res in results:
                title = res.get("title", "")
                # Ensure at least one significant word matches
                name_words = set(w.lower() for w in re.findall(r"\w{4,}", name))
                title_words = set(w.lower() for w in re.findall(r"\w{4,}", title))
                if name_words.intersection(title_words) or len(name) <= 6:
                    return title
    except Exception:
        pass
    return None


def translate_to_en(text_fr: str) -> str | None:
    """Translate French text into clean English using MyMemory with rotating academic quotas."""
    global current_email_idx
    if not text_fr or len(text_fr.strip()) < 10:
        return None

    # Clean text to 2 sentences for concise RAG / cards
    sentences = text_fr.split(".")
    clean_text = ". ".join(sentences[:2]).strip()
    if not clean_text.endswith("."):
        clean_text += "."
    if len(clean_text) > 400:
        clean_text = clean_text[:395] + "..."

    for _ in range(len(TRANSLATION_EMAILS)):
        email = TRANSLATION_EMAILS[current_email_idx % len(TRANSLATION_EMAILS)]
        try:
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": clean_text,
                "langpair": "fr|en",
                "de": email
            }
            r = requests.get(url, params=params, headers=HEADERS, timeout=8)
            if r.status_code == 200:
                data = r.json()
                trans = data.get("responseData", {}).get("translatedText", "")
                if trans and not trans.startswith("MYMEMORY WARNING:"):
                    return trans.strip()
                elif "MYMEMORY WARNING" in trans:
                    # Switch to next email quota
                    current_email_idx += 1
                    continue
        except Exception:
            current_email_idx += 1
            time.sleep(0.5)

    return None


def enrich_from_french(is_test=False, start_step=1):
    print("=" * 65)
    print(f"🇫🇷 Enriching Missing Places via French Wikipedia (Test: {is_test}, Start Step: {start_step})")
    print("=" * 65)

    if not INPUT_FILE.exists():
        print(f"❌ File not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        places = json.load(f)

    # Load checkpoint
    checkpoint = {}
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            print(f"Loaded checkpoint with {len(checkpoint)} cached results.")
        except Exception:
            checkpoint = {}

    missing_indices = [i for i, p in enumerate(places) if not p.get("description")]
    print(f"Places without description: {len(missing_indices)} / {len(places)}")

    # Resolve start_step if string (e.g., place name like 'el-Mida') was passed
    if isinstance(start_step, str):
        if start_step.isdigit():
            start_step = int(start_step)
        else:
            query = start_step.lower().strip()
            found = False
            for s, idx in enumerate(missing_indices, start=1):
                p_name = (places[idx].get("name_en") or places[idx].get("name") or "").lower()
                if query in p_name:
                    start_step = s
                    found = True
                    print(f"🎯 Matched '{query}' ➔ Starting directly at Step {start_step} ({places[idx].get('name_en')})")
                    break
            if not found:
                print(f"⚠️ Could not find place matching '{start_step}'. Defaulting to start.")
                start_step = 1

    # Clear cached failed results for start_step onwards
    if start_step > 1:
        cleared = 0
        for idx in missing_indices[start_step - 1:]:
            pid = places[idx].get("id", str(idx))
            if pid in checkpoint:
                del checkpoint[pid]
                cleared += 1
        if cleared > 0:
            print(f"🧹 Cleared {cleared} cached entries from step {start_step}+ to allow fresh translation.")

    if is_test:
        start_idx = max(0, start_step - 1)
        target_indices = missing_indices[start_idx : start_idx + 3]
        step_offset = start_step
    else:
        target_indices = missing_indices
        step_offset = 1

    enriched_count = 0

    for step, idx in enumerate(target_indices, start=step_offset):
        place = places[idx]
        name_en = place.get("name_en") or place.get("name") or ""
        name_fr = place.get("name_fr") or name_en
        pid = place.get("id", str(idx))

        # Check cached checkpoint (only if before start_step)
        if step < start_step and pid in checkpoint:
            cached_desc = checkpoint[pid]
            if cached_desc:
                place["description"] = cached_desc
                enriched_count += 1
            continue

        fr_summary = None

        # 1. Check if direct French title in wikipedia_url
        wiki_url = place.get("wikipedia_url", "")
        if "fr.wikipedia.org/wiki/" in wiki_url:
            raw_title = wiki_url.split("/wiki/")[-1]
            title = urllib.parse.unquote(raw_title)
            fr_summary = get_fr_summary(title)

        # 2. Search French Wikipedia using name_fr
        if not fr_summary and name_fr:
            time.sleep(0.3)
            found_title = search_fr_wikipedia(name_fr)
            if found_title:
                time.sleep(0.3)
                fr_summary = get_fr_summary(found_title)

        # 3. Search French Wikipedia using name_en as fallback
        if not fr_summary and name_en and name_en != name_fr:
            time.sleep(0.3)
            found_title = search_fr_wikipedia(name_en)
            if found_title:
                time.sleep(0.3)
                fr_summary = get_fr_summary(found_title)

        # 4. Translate FR -> EN
        en_description = ""
        if fr_summary:
            time.sleep(0.4)
            translated = translate_to_en(fr_summary)
            if translated:
                en_description = translated
                place["description"] = en_description
                enriched_count += 1
                print(f"[{step}/{len(target_indices)}] ✅ {name_en}:")
                print(f"    EN: {en_description[:100]}...")
            else:
                print(f"[{step}/{len(target_indices)}] ⚠️ Found FR text, but translation failed for {name_en}")
        else:
            if step % 20 == 0 or is_test:
                print(f"[{step}/{len(target_indices)}] —— No article found for {name_en} ({name_fr})")

        checkpoint[pid] = en_description

        # Save checkpoint periodically
        if step % 15 == 0 and not is_test:
            with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, ensure_ascii=False)
            with open(INPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(places, f, ensure_ascii=False, indent=2)

    # Final save
    if not is_test:
        with open(INPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(places, f, ensure_ascii=False, indent=2)
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, ensure_ascii=False)

    print("\n" + "─" * 65)
    print(f"🎉 Enriched: {enriched_count} new places with descriptions!")
    print(f"📄 Output updated: {INPUT_FILE}")


if __name__ == "__main__":
    test_mode = "--test" in sys.argv
    start_arg = 1
    for i, arg in enumerate(sys.argv):
        if arg == "--start" and i + 1 < len(sys.argv):
            start_arg = sys.argv[i + 1]
    enrich_from_french(is_test=test_mode, start_step=start_arg)
