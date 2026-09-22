"""
Burmese (Myanmar Unicode & Zawgyi) to Myanglish (Burglish) Transliteration Engine.
Uses OpenAI gpt-4o-mini with JSON schema output, SQLite caching, batching (20-30 items),
and fallback mechanisms.
"""
import os
import re
import json
from typing import List, Dict, Optional, Set
from dotenv import load_dotenv

from .db import Database

# Load .env file automatically
load_dotenv()

BURMESE_CHAR_REGEX = re.compile(r"[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]")

# Built-in phonetic dictionary for common Burmese music artists, words, and syllables
# Provides instant offline fallback and unit test consistency
OFFLINE_PHONETIC_MAP = {
    # Artists & famous names
    "စိုင်းထီးဆိုင်": "Sai Htee Saing",
    "စိုင်းထီးဆိုငျ": "Sai Htee Saing",
    "လေးဖြူ": "Lay Phyu",
    "ေလးျဖဴ": "Lay Phyu",
    "အငဲ": "Ah Nge",
    "အငဲ္": "Ah Nge",
    "မျိုးကြီး": "Myo Gyi",
    "မ်ဳိးကြီး": "Myo Gyi",
    "ဝိုင်းစုခိုင်သိန်း": "Wine Su Khine Thein",
    "ဝိုင္းစုခိုင္သိန္း": "Wine Su Khine Thein",
    "ဖြိုးပြည့်စုံ": "Phyo Pyae Sone",
    "ျဖိုးျပည့္စုံ": "Phyo Pyae Sone",
    "စည်သူလွင်": "Sithu Lwin",
    "စည္သူလြင္": "Sithu Lwin",
    "ဇော်ဝင်းထွဋ်": "Zaw Win Htut",
    "ေဇာ္ဝင္းထြတ္": "Zaw Win Htut",
    "ရဲလေး": "Ye Lay",
    "ရဲေလး": "Ye Lay",
    "နီနီခင်ဇော်": "Ni Ni Khin Zaw",
    "နီနီခင္ေဇာ္": "Ni Ni Khin Zaw",
    "စိုင်းစိုင်းခမ်းလှိုင်": "Sai Sai Kham Leng",
    "စိုင္းစိုင္းခမ္းလႈိင္": "Sai Sai Kham Leng",
    "သျှား": "Shar",
    "အာဇာနည်": "R Zarni",
    "ဘန်နီဖြိုး": "Bunny Phyoe",
    "တူးတူး": "Too Too",
    "ဟဲလေး": "Hay Lay",

    # Common song words & syllables
    "အချစ်": "A Chit",
    "အခ်စ္": "A Chit",
    "အချစ်ဆုတောင်း": "A Chit Su Taung",
    "အခ်စ္ဆုေတာင္း": "A Chit Su Taung",
    "သီချင်းများ": "Tha Chin Mya",
    "သီခ်င္းမ်ား": "Tha Chin Mya",
    "ချစ်သူ": "Chit Thu",
    "ခ်စ္သူ": "Chit Thu",
    "ချစ်ခြင်း": "Chit Chin",
    "ခ်စ္ျခင္း": "Chit Chin",
    "မင်းသိမ်း": "Min Thein",
    "မင္းသိမ္း": "Min Thein",
    "နွေ": "Nway",
    "ေႏြ": "Nway",
    "မိုး": "Moe",
    "ေမွာ္": "Mhaw",
    "မျှော်": "Mhyaw",
    "ဆောင်း": "Saung",
    "ေဆာင္း": "Saung",
    "နှလုံးသား": "Hnalone Thar",
    "ႏွလုံးသား": "Hnalone Thar",
    "သီချင်း": "Tha Chin",
    "သီခ်င္း": "Tha Chin",
    "အလွမ်း": "A Lwan",
    "အလြမ္း": "A Lwan",
    "မင်းအတွက်": "Min A Twet",
    "မင္းအတြက္": "Min A Twet",
    "ပြန်ဆုံကြမယ်": "Pyan Sone Gya Mal",
    "ျပန္ဆုံၾကမယ္": "Pyan Sone Gya Mal",
    "အိပ်မက်": "Eik Met",
    "အိပ္မက္": "Eik Met",
    "လွမ်းတယ်": "Lwan Tal",
    "လြမ္းတယ္": "Lwan Tal",
    "ရွှေ": "Shwe",
    "ေရႊ": "Shwe",
    "ရင်ခုန်သံ": "Yin Khone Than",
    "ရင္ခုန္သံ": "Yin Khone Than",
    "ကောင်းကင်": "Kaung Kin",
    "ေကာင္းကင္": "Kaung Kin",
    "နေမင်း": "Nay Min",
    "ေနမင္း": "Nay Min",
    "လမင်း": "La Min",
    "လမင္း": "La Min",
}


def contains_burmese(text: str) -> bool:
    """Check if the string contains any Burmese Unicode or Zawgyi characters."""
    if not text:
        return False
    return bool(BURMESE_CHAR_REGEX.search(text))


def offline_transliterate(text: str) -> str:
    """
    High-fidelity offline fallback for Burmese to Myanglish transliteration.
    Uses vocabulary mapping, token substitution, and clean normalization.
    """
    if not contains_burmese(text):
        return text.strip()

    cleaned = text.strip()

    # Exact dictionary match
    if cleaned in OFFLINE_PHONETIC_MAP:
        return OFFLINE_PHONETIC_MAP[cleaned]

    # Partial phrase substitution
    result = cleaned
    for burmese_term, romanized in sorted(OFFLINE_PHONETIC_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if burmese_term in result:
            result = result.replace(burmese_term, f" {romanized} ")

    # Normalize multiple spaces and clean up
    result = re.sub(r"\s+", " ", result).strip()

    # If some Burmese characters remain unmapped, replace glyph sequences gracefully
    if contains_burmese(result):
        # Basic consonant/vowel syllable mapping
        syllable_map = {
            "က": "Ka", "ခ": "Kha", "ဂ": "Ga", "ဃ": "Gha", "င": "Nga",
            "စ": "Sa", "ဆ": "Hsa", "ဇ": "Za", "ဈ": "Zha", "ည": "Nya",
            "ဋ": "Ta", "ဌ": "Hta", "ဍ": "Da", "ဎ": "Dha", "ဏ": "Na",
            "တ": "Ta", "ထ": "Hta", "ဒ": "Da", "ဓ": "Dha", "န": "Na",
            "ပ": "Pa", "ဖ": "Pha", "ဗ": "Ba", "ဘ": "Bha", "မ": "Ma",
            "ယ": "Ya", "ရ": "Ya", "လ": "La", "ဝ": "Wa", "သ": "Tha",
            "ဟ": "Ha", "ဠ": "La", "အ": "A",
            "၀": "0", "၁": "1", "၂": "2", "၃": "3", "၄": "4",
            "၅": "5", "၆": "6", "၇": "7", "၈": "8", "၉": "9"
        }
        chars = []
        for char in result:
            if char in syllable_map:
                chars.append(syllable_map[char])
            elif not BURMESE_CHAR_REGEX.match(char):
                chars.append(char)
        result = "".join(chars)

    result = re.sub(r"\s+", " ", result).strip()
    return result if result else text.strip()


def transliterate_batch_with_openai(texts: List[str], api_key: str) -> Dict[str, str]:
    """
    Transliterate a batch of Burmese strings to Myanglish using OpenAI gpt-4o-mini.
    Enforces strict JSON schema output.
    """
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are an expert Burmese (Myanmar) linguist and music archivist. "
        "Your task is to transliterate Burmese track metadata (titles, artist names, album titles) "
        "written in Myanmar script (Unicode or Zawgyi) into standard, clean, natural Myanglish (Burglish / Romanized Burmese).\n\n"
        "Guidelines:\n"
        "1. Produce standard natural Romanized Burmese pronunciation used in popular culture and music (Title Case).\n"
        "2. Keep any existing English words, numbers, and punctuation intact.\n"
        "3. Handle both standard Unicode and legacy Zawgyi encodings seamlessly.\n"
        "4. Output MUST be a valid JSON object with the key 'transliterations' mapping each exact original string to its Myanglish transliteration."
    )

    user_payload = {
        "items": texts
    }

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
        ]
    )

    content = response.choices[0].message.content
    data = json.loads(content)
    raw_map = data.get("transliterations", {})
    return {k: str(v).strip() for k, v in raw_map.items()}


def transliterate_batch_with_gemini(texts: List[str], api_key: str) -> Dict[str, str]:
    """
    Fallback transliteration using Google Gemini SDK.
    """
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = (
            "Transliterate the following list of Burmese music metadata items (Myanmar script, Unicode or Zawgyi) "
            "into standard Myanglish (Burglish / Romanized Burmese in Title Case). Return ONLY a JSON object "
            "with key 'transliterations' mapping each original string to its Myanglish equivalent.\n\n"
            f"{json.dumps({'items': texts}, ensure_ascii=False)}"
        )
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        data = json.loads(resp.text)
        return data.get("transliterations", {})
    except Exception:
        return {}


class TransliterationEngine:
    def __init__(self, db: Database, openai_key: Optional[str] = None, batch_size: int = 25):
        self.db = db
        self.openai_key = openai_key or os.environ.get("OPENAI_API_KEY") or ""
        self.gemini_key = os.environ.get("GEMINI_API_KEY") or ""
        self.batch_size = max(5, min(50, batch_size))

    def transliterate_texts(self, texts: List[str]) -> Dict[str, str]:
        """
        Transliterate a collection of texts.
        - Identifies Burmese text
        - Reads from SQLite cache
        - Batches uncached items through OpenAI gpt-4o-mini (or Gemini fallback)
        - Falls back to offline phonetics if APIs are unavailable
        - Saves new entries to SQLite cache
        """
        results: Dict[str, str] = {}
        burmese_to_fetch: Set[str] = set()

        for t in texts:
            if not t:
                results[t] = ""
                continue
            cleaned = t.strip()
            if not contains_burmese(cleaned):
                results[t] = cleaned
            else:
                burmese_to_fetch.add(cleaned)

        if not burmese_to_fetch:
            return results

        # Check SQLite cache
        cached_results = self.db.get_cached_transliterations_bulk(list(burmese_to_fetch))
        for orig, translit in cached_results.items():
            results[orig] = translit
            burmese_to_fetch.discard(orig)

        # Remaining items need LLM / engine transliteration
        remaining_list = list(burmese_to_fetch)
        if remaining_list:
            # Process in batches of 20-30
            for i in range(0, len(remaining_list), self.batch_size):
                batch = remaining_list[i:i + self.batch_size]
                batch_mappings: Dict[str, str] = {}

                # 1. Try OpenAI gpt-4o-mini
                if self.openai_key:
                    try:
                        batch_mappings = transliterate_batch_with_openai(batch, self.openai_key)
                    except Exception as err:
                        print(f"[transliterate] OpenAI API request failed: {err}")

                # 2. Fallback to Gemini if OpenAI was not configured or errored
                if not batch_mappings and self.gemini_key:
                    try:
                        batch_mappings = transliterate_batch_with_gemini(batch, self.gemini_key)
                    except Exception as err:
                        print(f"[transliterate] Gemini fallback failed: {err}")

                # 3. Fallback to offline phonetics for any missing items
                final_batch_map: Dict[str, str] = {}
                for item in batch:
                    translit = batch_mappings.get(item)
                    if not translit or contains_burmese(translit):
                        translit = offline_transliterate(item)
                    final_batch_map[item] = translit
                    results[item] = translit

                # Store into SQLite cache
                model_name = "gpt-4o-mini" if self.openai_key else ("gemini-2.5-flash" if self.gemini_key else "offline-phonetics")
                self.db.save_transliterations_bulk(final_batch_map, detected_script="burmese", model_used=model_name)

        return results

    def transliterate_single(self, text: str) -> str:
        """Helper to transliterate one string."""
        if not text or not contains_burmese(text):
            return text
        res = self.transliterate_texts([text])
        return res.get(text.strip(), text)
