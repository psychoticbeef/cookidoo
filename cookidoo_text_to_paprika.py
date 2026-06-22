#!/usr/bin/env python3
"""Convert a Cookidoo recipe into a Paprika file from rendered-browser TEXT.

Why a text version: Cookidoo's "Meine Notizen" (and the recipe body) are loaded
into the page after the fact and are NOT in the page source you can view/save.
But they ARE in what the browser actually renders. So the most reliable input
is a plain-text copy of the open recipe page (e.g. select-all + copy, or
`pbpaste`), which contains every visible field including your custom notes.

Usage:
    pbpaste | python3 cookidoo_text_to_paprika.py --url <recipe-url>
    python3 cookidoo_text_to_paprika.py --url <recipe-url> --text page.txt

The title image is not in the text, so it is recovered separately: the recipe
page exposes a public ``og:image``/``og:title`` in its <head> even without a
login, which is fetched with the system ``curl`` utility.

Mapping of the custom "Meine Notizen" (per request):
    * the "Nährwerte" paragraph   -> nutritional_info
    * the "Einfrieren:" paragraph  -> description
    * everything else             -> discarded
The official on-page "Nährwerte" section is never used.

Only the Python standard library is used for parsing; ``curl`` does downloads.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import unicodedata
from urllib.parse import urlparse

from paprika_recipes import Recipe


# Cookidoo renders Thermomix cooking-mode icons (and all UI chrome) with an
# icon font mapped onto Unicode Private-Use-Area codepoints. Those render as an
# icon on the site but as tofu everywhere else. For the meaningful inline
# cooking-mode glyphs we want to KEEP an icon, so map their codepoint to a real
# emoji (which renders in Paprika). Any PUA glyph not listed here is treated as
# UI chrome and removed.
#
# Discover a codepoint by copying a step and running:
#   pbpaste | python3 -c "import sys;[print(hex(ord(c))) for c in sys.stdin.read() if 0xE000<=ord(c)<=0xF8FF]"
# The class->codepoint map can also be read straight from Cookidoo's icon CSS
# (see build_icon_css_map.py / scripts that grep `.icon--NAME{content:"\\eXXX"}`).
ICON_MAP = {
    # codepoint : (German Thermomix mode label, emoji or "")
    # Rendered inline as "[label] emoji" (or just "[label]" when no emoji).
    # Names come from Cookidoo's --plcore-icon-* CSS (see cookidoo-icon-codepoints.tsv);
    # UI-chrome icons are omitted so sanitize() strips them.
    "\ue001":   ("Teigstufe", "🥨"),
    "\ue002":   ("Rührstufe", "🥄"),
    "\ue003":   ("Linkslauf", "🔄"),
    "\ue004":   ("Linkslauf aus", ""),
    "\ue008":   ("Dampfgaren", "♨️"),
    "\ue00a":   ("Spatel", "🥄"),
    "\ue00b":   ("Turbo", "⚡"),
    "\ue00c":   ("Karamellisieren", "🍮"),
    "\ue00d":   ("Reis", "🍚"),
    "\ue011":   ("Reinigen", "🧼"),
    "\ue012":   ("Sahne", "🥛"),
    "\ue014":   ("Heißrühren", "🔥"),
    "\ue016":   ("Wasserkocher", "🫖"),
    "\ue018":   ("Langsames Garen", "🍲"),
    "\ue019":   ("Erwärmen", "🔥"),
    "\ue01e":   ("Kalt mixen", "🧊"),
    "\ue02d":   ("Sous-vide", "🌡️"),
    "\ue02e":   ("Fermentieren", "🫙"),
    "\ue031":   ("Andicken", "🍶"),
    "\ue033":   ("Eierkochen", "🥚"),
    "\ue036":   ("Reiben", "🧀"),
    "\ue037":   ("Schneiden", "🔪"),
    "\ue038":   ("Schälen", "🔪"),
    "\ue03a":   ("Automatik", "✨"),
    "\ue03c":   ("Gareinsatz", "🧺"),
    "\ue03d":   ("Varoma", "♨️"),
    "\ue04c":   ("Spiralschneiden", "🌀"),
}


def _apply_icon_map(text: str) -> str:
    for codepoint, (label, emoji) in ICON_MAP.items():
        replacement = f"[{label}] {emoji}" if emoji else f"[{label}]"
        text = text.replace(codepoint, replacement)
    return text


def sanitize(text: str) -> str:
    """Map known cooking-mode icons to emoji, drop other icon-font junk.

    Cookidoo renders its UI icons (servings, the hamburger menu, equipment
    hints like a gravy boat, etc.) with an icon font mapped onto Unicode
    Private-Use-Area codepoints. When the page text is copied those PUA
    codepoints come along and render as garbage (tofu / hamburger-menu shapes)
    in any other font. Glyphs listed in ICON_MAP are first turned into a real
    emoji; then everything still in the Unicode "Other" categories (Cc control,
    Cf format, Co private-use, Cs surrogate, Cn unassigned) is stripped, while
    newlines/tabs, letters, punctuation, ®, and genuine emoji (category So) are
    preserved.
    """
    if not text:
        return text
    text = _apply_icon_map(text)
    kept = []
    for ch in text:
        if ch in "\n\t\ufe0f\u200d":   # keep newlines + emoji VS16/ZWJ joiners
            kept.append(ch)
        elif unicodedata.category(ch)[0] != "C":
            kept.append(ch)
    cleaned = "".join(kept)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in cleaned.split("\n")]
    return "\n".join(lines).strip()


# Cookidoo difficulty labels -> Paprika's German scale.
_DIFFICULTY_MAP = {"einfach": "Leicht", "medium": "Mittel"}


def map_difficulty(value: str) -> str:
    """Normalize a Cookidoo difficulty (e.g. 'einfach', 'medium')."""
    return _DIFFICULTY_MAP.get(value.strip().lower(), value)


def digits_only(value: str) -> str:
    """Keep just the number, e.g. '4 Portionen' -> '4'."""
    m = re.search(r"\d+", value or "")
    return m.group(0) if m else ""


def to_minutes(value: str) -> str:
    """Total minutes as an integer string: '4 Std.' -> '240',
    '1 Std. 35 Min' -> '95', '30 Min' -> '30'. '' if no number."""
    if not value:
        return ""
    h = re.search(r"(\d+)\s*(?:Std|Stunden?)\b", value, re.IGNORECASE)
    m = re.search(r"(\d+)\s*(?:Min|Minuten?)\b", value, re.IGNORECASE)
    if h or m:
        return str((int(h.group(1)) if h else 0) * 60 + (int(m.group(1)) if m else 0))
    n = re.search(r"\d+", value)   # no unit -> assume minutes
    return n.group(0) if n else ""


def servings_from_yield(value: str) -> str:
    """Servings from a yield: a bare number for portion counts
    ('4 Portionen' -> '4', '16 Stücke' -> '16'), but the verbatim text for
    weight/volume yields ('325 g' -> '325 g'), whose number is a quantity,
    not a serving count."""
    if re.search(r"\b\d+\s*(?:g|kg|mg|ml|l|liter)\b", value or "", re.IGNORECASE):
        return value.strip()
    return digits_only(value)


# --------------------------------------------------------------------------
# system curl helpers (public page head + image bytes)
# --------------------------------------------------------------------------
def curl_text(url: str) -> str:
    proc = subprocess.run(
        ["curl", "-fsSL", "--max-time", "30", url], capture_output=True
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode(errors="replace").strip() or f"exit {proc.returncode}")
    return proc.stdout.decode("utf-8", errors="replace")


def curl_bytes(url: str) -> bytes:
    proc = subprocess.run(
        ["curl", "-fsSL", "--max-time", "30", url], capture_output=True
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode(errors="replace").strip() or f"exit {proc.returncode}")
    if not proc.stdout:
        raise RuntimeError("curl returned no data")
    return proc.stdout


def fetch_meta(url: str):
    """Return (og_title, og_image) from the public page head, or ('', '')."""
    try:
        page = curl_text(url)
    except RuntimeError:
        return "", ""

    def meta(prop):
        m = re.search(r'<meta property="%s" content="([^"]*)"' % re.escape(prop), page)
        return html.unescape(m.group(1)) if m else ""

    return meta("og:title"), meta("og:image")


# --------------------------------------------------------------------------
# text parsing
# --------------------------------------------------------------------------
def find_header(lines, header, start=0):
    """Index of the first line that equals `header` exactly (stripped)."""
    for i in range(start, len(lines)):
        if lines[i].strip() == header:
            return i
    return -1


def nonempty(seq):
    return [s.strip() for s in seq if s.strip()]


def parse_ingredients(block):
    """Group ingredient lines into 'amount name, description' entries.

    Each ingredient is a run of non-blank lines (the site separates them with a
    blank line): first line = name, last line = amount, middle lines = note.
    """
    items, group = [], []
    for raw in block:
        if raw.strip():
            group.append(raw.strip())
        elif group:
            items.append(group)
            group = []
    if group:
        items.append(group)

    out = []
    for g in items:
        if len(g) == 1:
            out.append(g[0])
            continue
        name, amount, desc = g[0], g[-1], g[1:-1]
        line = f"{amount} {name}".strip()
        if desc:
            line += ", " + ", ".join(desc)
        out.append(line)
    return "\n".join(out)


def parse_meine_notizen(block):
    """Split the custom-notes block into (nutrition, freezer) by paragraph.

    Paragraphs are separated by blank lines. The paragraph whose first line
    starts with 'Nährwerte' becomes nutrition (header + values kept verbatim);
    the one starting with 'Einfrieren' becomes the freezer note. The rest is
    discarded.
    """
    paragraphs, cur = [], []
    for raw in block:
        if raw.strip():
            cur.append(raw.rstrip())
        elif cur:
            paragraphs.append(cur)
            cur = []
    if cur:
        paragraphs.append(cur)

    nutrition, freezer = "", ""
    for p in paragraphs:
        head = p[0].strip().lower().replace("ä", "a").replace("ae", "a")
        if head.startswith("nahrwerte") and not nutrition:
            nutrition = "\n".join(p).strip()
        elif head.startswith("einfrieren") and not freezer:
            freezer = "\n".join(p).strip()
    return nutrition, freezer


def first_match(text, pattern):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else ""


# --------------------------------------------------------------------------
# optional HTML enrichment (precise ingredients incl. alternatives + gallery)
# --------------------------------------------------------------------------
ALT_MARKER = "[oder]"  # how an ingredient alternative is introduced


def _html_text(fragment: str) -> str:
    t = re.sub(r"(?is)<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def _span(block: str, cls: str) -> str:
    m = re.search(r'<span class="%s">(.*?)</span>' % re.escape(cls), block, re.DOTALL)
    return _html_text(m.group(1)) if m else ""


def parse_ingredients_html(html_text: str) -> str:
    """Parse <recipe-ingredient> blocks: amount + name (+ description), and an
    'oder' alternative when a recipe-ingredient__alternative span is present."""
    out = []
    for block in re.findall(r"<recipe-ingredient>(.*?)</recipe-ingredient>", html_text, re.DOTALL):
        name = _span(block, "recipe-ingredient__name")
        if not name:
            continue
        amount = _span(block, "recipe-ingredient__amount")
        desc = _span(block, "recipe-ingredient__description")
        alt = _span(block, "recipe-ingredient__alternative")
        line = (amount + " " + name).strip()
        if desc:
            line += ", " + desc
        if alt:
            line += f" {ALT_MARKER} {alt}"
        out.append(line)
    return "\n".join(out)


def html_to_markdown(text: str) -> str:
    """Inline HTML -> Paprika markdown: <strong>/<b> -> **bold**,
    <em>/<i> -> *italic*; other tags removed, entities decoded."""
    if not text:
        return ""
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</?(?:strong|b)\b[^>]*>", "**", text)
    text = re.sub(r"(?i)</?(?:em|i)\b[^>]*>", "*", text)
    text = re.sub(r"<[^>]+>", "", text)        # drop the rest (e.g. <nobr>)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _ld_recipe(html_text: str) -> dict:
    """The ld+json Recipe object from the page, or None."""
    for m in re.finditer(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html_text, re.DOTALL | re.IGNORECASE,
    ):
        try:
            obj = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        t = obj.get("@type") if isinstance(obj, dict) else None
        if t == "Recipe" or (isinstance(t, list) and "Recipe" in t):
            return obj
    return None


def extract_directions_ld(html_text: str) -> str:
    """Directions from the page's ld+json, keeping <strong> as **bold** and
    HowToSection names as bold sub-headings. '' if not found.  Plain text from
    the copied page loses bold, so the HTML is the only source for it."""
    recipe = _ld_recipe(html_text) if html_text else None
    if not recipe:
        return ""
    out = []

    def walk(items):
        for step in items or []:
            if not isinstance(step, dict):
                t = html_to_markdown(str(step))
                if t:
                    out.append(t)
            elif step.get("@type") == "HowToSection" or step.get("itemListElement"):
                name = html_to_markdown(step.get("name", ""))
                if name:
                    out.append(f"**{name}**")
                walk(step.get("itemListElement"))
            else:
                t = html_to_markdown(step.get("text", ""))
                if t:
                    out.append(t)

    walk(recipe.get("recipeInstructions"))
    return "\n\n".join(out)


def extract_recipe_images_html(html_text: str) -> list:
    """Unique recipe gallery picture URLs (the <img class="recipe-card__image">
    elements), upgraded to the higher-resolution derivative. Related-recipe
    tiles, collection thumbnails, ingredient icons and the video are excluded
    because they do not use this class / image token."""
    urls = []
    for tag in re.findall(r'<img[^>]*class="recipe-card__image"[^>]*>', html_text):
        m = re.search(r'src="([^"]+)"', tag)
        if not m:
            continue
        u = m.group(1).replace("/t_web_rdp_recipe_584x480/", "/t_web_rdp_recipe_584x480_1_5x/")
        if u not in urls:
            urls.append(u)
    return urls


def extract_devices(html_text: str) -> tuple:
    """Return ``(devices, accessories)`` from the 'Geräte und Zubehör' block.

    Thermomix versions (TM5/TM6/TM7...) are devices; entries of any other type
    are additional Zubehör (Varoma, Gareinsatz, ...).
    """
    devices, accessories = [], []
    block = re.search(
        r"<rdp-devices-and-accessories\b.*?</rdp-devices-and-accessories>",
        html_text, re.DOTALL | re.IGNORECASE,
    )
    if block:
        for dm in re.finditer(
            r"<recipe-device\b([^>]*)>(.*?)</recipe-device>",
            block.group(0), re.DOTALL | re.IGNORECASE,
        ):
            nm = re.search(r'class="recipe-device__name">(.*?)</span>', dm.group(2), re.DOTALL)
            if not nm:
                continue
            name = re.sub(r"\s+", " ", html.unescape(nm.group(1))).strip()
            if not name:
                continue
            t = re.search(r'type="([^"]*)"', dm.group(1))
            if t and t.group(1).strip().lower() == "thermomixversion":
                devices.append(name)
            else:
                accessories.append(name)
    # Separate "Notwendiges Zubehör" list (Springform, Backpapier, ...).
    useful = re.search(
        r'class="[^"]*recipe-content__useful-items[^"]*".*?<ul[^>]*>(.*?)</ul>',
        html_text, re.DOTALL | re.IGNORECASE,
    )
    if useful:
        for li in re.findall(r"<li>(.*?)</li>", useful.group(1), re.DOTALL):
            name = re.sub(r"\s+", " ", html.unescape(li)).strip()
            if name:
                accessories.append(name)
    return devices, accessories


def devices_from_text(lines: list) -> tuple:
    """Classify a plain-text 'Geräte und Zubehör' block: ``TM<n>`` = device, rest Zubehör."""
    devices, accessories = [], []
    for ln in nonempty(lines):
        ln = ln.strip()
        if ln == "Notwendiges Zubehör":   # sub-header inside the section, not an item
            continue
        if re.fullmatch(r"TM\s*\d+", ln):
            devices.append(ln)
        else:
            accessories.append(ln)
    return devices, accessories


def devices_note(devices: list, accessories: list) -> str:
    """Format devices/accessories as note lines (empty string if none)."""
    parts = []
    if devices:
        parts.append("Geräte: " + ", ".join(devices))
    if accessories:
        parts.append("Zubehör: " + ", ".join(accessories))
    return "\n".join(parts)


def build_recipe(url: str, text: str, html_text: str = None, fetch_image: bool = True) -> Recipe:
    # Strip icon-font junk (mapping known mode icons to emoji) up front so it
    # can't sit in front of a section header and defeat detection.
    text = sanitize(text)
    lines = text.splitlines()
    full = "\n".join(lines)

    # --- name + image from the public page head (login not required) --------
    og_title, og_image = fetch_meta(url) if (url and fetch_image) else ("", "")

    # --- section anchors ----------------------------------------------------
    i_zutaten = find_header(lines, "Zutaten")
    i_geraete = find_header(lines, "Geräte und Zubehör")
    i_schwier = find_header(lines, "Schwierigkeitsgrad")
    i_zub = find_header(lines, "Zubereitung")          # exact -> the steps header
    i_tipps = find_header(lines, "Tipps")
    i_notizen = find_header(lines, "Meine Notizen")
    i_teilen = find_header(lines, "Rezept teilen")
    i_tags = find_header(lines, "Ähnliche Rezepte finden")
    i_auch = find_header(lines, "Auch enthalten in")

    # --- ingredients (HTML is precise: names/amounts/alternatives) ----------
    ingredients = ""
    if html_text:
        ingredients = parse_ingredients_html(html_text)
    if not ingredients and i_zutaten != -1 and i_geraete > i_zutaten:
        ingredients = parse_ingredients(lines[i_zutaten + 1 : i_geraete])

    # --- directions ---------------------------------------------------------
    # The HTML keeps <strong> emphasis + section headings (-> markdown); the
    # copied plain text has lost the bold, so fall back to it only without HTML.
    directions = extract_directions_ld(html_text) if html_text else ""
    if not directions and i_zub != -1 and i_tipps > i_zub:
        directions = "\n\n".join(nonempty(lines[i_zub + 1 : i_tipps]))

    # --- difficulty ---------------------------------------------------------
    difficulty = ""
    if i_schwier != -1:
        rest = nonempty(lines[i_schwier + 1 : i_schwier + 4])
        difficulty = rest[0] if rest else ""

    # --- tips -> notes ------------------------------------------------------
    notes = ""
    if i_tipps != -1 and i_notizen > i_tipps:
        notes = "\n".join(nonempty(lines[i_tipps + 1 : i_notizen]))

    # --- devices + accessories -> top of notes ------------------------------
    devices, accessories = [], []
    if html_text:
        devices, accessories = extract_devices(html_text)
    if not devices and not accessories and i_geraete != -1 and i_schwier > i_geraete:
        devices, accessories = devices_from_text(lines[i_geraete + 1 : i_schwier])
    dev_note = devices_note(devices, accessories)
    if dev_note:
        notes = (dev_note + "\n\n" + notes).strip() if notes else dev_note

    # --- custom notes: Nährwerte -> nutrition, Einfrieren -> description -----
    nutrition, freezer = "", ""
    if i_notizen != -1:
        end = i_teilen if i_teilen > i_notizen else len(lines)
        i_land = find_header(lines, "Land", i_notizen)
        if i_land != -1 and i_land < end:
            end = i_land
        nutrition, freezer = parse_meine_notizen(lines[i_notizen + 1 : end])
    description = freezer

    # --- categories (visible tags) ------------------------------------------
    categories = []
    if i_tags != -1:
        end = i_auch if i_auch > i_tags else i_tags + 12
        categories = nonempty(lines[i_tags + 1 : end])

    # --- scalar fields via regex over the whole text ------------------------
    # Prefer the explicit "Portionsgröße <yield>" line (covers Portionen, Stücke,
    # weight yields like '325 g'); fall back to a bare "N Portionen".
    servings = (first_match(full, r"Portionsgröße\s+(\d[^\n]*)")
                or first_match(full, r"(\d+\s+Portionen)"))
    # Capture the whole duration phrase (incl. 'Std.') starting at the first digit.
    prep_time = first_match(full, r"Zubereitung\s+(\d[^\n]*)")
    total_time = first_match(full, r"Gesamt\s+(\d[^\n]*)")

    rating = 0
    m = re.search(r"(\d[.,]?\d?)\s*\n\s*\d+\s+Bewertungen", full)
    if m:
        rating = int(float(m.group(1).replace(",", ".")) + 0.5)

    name = og_title.strip()
    if not name:
        if m:
            before = nonempty(full[: m.start()].splitlines())
            name = before[-1] if before else "Recipe"
        else:
            name = "Recipe"

    recipe = Recipe(
        name=sanitize(name) or "Recipe",
        ingredients=sanitize(ingredients),
        directions=sanitize(directions),
        description=sanitize(description),
        servings=servings_from_yield(sanitize(servings)),
        prep_time=to_minutes(sanitize(prep_time)),
        total_time=to_minutes(sanitize(total_time)),
        difficulty=map_difficulty(sanitize(difficulty)),
        notes=sanitize(notes),
        categories=[c for c in (sanitize(c) for c in categories) if c],
        rating=rating,
        source=urlparse(url).netloc or "cookidoo.de",
        source_url=url,
        image_url=og_image,
    )
    if nutrition:
        recipe.nutritional_info = sanitize(nutrition)

    # --- pictures -----------------------------------------------------------
    # With HTML we get the whole gallery (all pictures, video excluded); without
    # it we only have the single public og:image. First picture = title photo,
    # the rest go into Paprika's photos[] array.
    image_urls = extract_recipe_images_html(html_text) if html_text else []
    if not image_urls and og_image:
        image_urls = [og_image]
    if image_urls:
        recipe.image_url = image_urls[0]

    if fetch_image:
        for idx, u in enumerate(image_urls):
            try:
                data = curl_bytes(u)
                fname = os.path.basename(urlparse(u).path) or f"photo{idx}.jpg"
                if not os.path.splitext(fname)[1]:
                    fname += ".jpg"
                if idx == 0:
                    recipe.set_photo(data, filename=fname)
                else:
                    recipe.add_photo(data, name=str(idx + 1), filename=fname)
                print(f"Downloaded picture {idx + 1}/{len(image_urls)} ({len(data)} bytes).", file=sys.stderr)
            except RuntimeError as e:
                print(f"Warning: could not download picture {idx + 1}: {e}", file=sys.stderr)

    return recipe


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Convert a Cookidoo recipe (rendered browser text) to a Paprika file."
    )
    ap.add_argument("--url", required=True, help="The recipe page URL.")
    ap.add_argument(
        "--text",
        default="-",
        help="Path to a file with the copied page text, or '-' for stdin "
        "(default; use with `pbpaste | ...`).",
    )
    ap.add_argument("--out", help="Output .paprikarecipes path (default: <name>.paprikarecipes).")
    ap.add_argument(
        "--html",
        help="Optional page HTML file: enables ALL gallery pictures and precise "
        "ingredients (with 'oder' alternatives). Without it, only the single "
        "public title image and text-parsed ingredients are used.",
    )
    ap.add_argument("--no-image", action="store_true", help="Do not download pictures.")
    args = ap.parse_args(argv)

    if args.text == "-":
        text = sys.stdin.read()
    else:
        with open(args.text, "r", encoding="utf-8") as fh:
            text = fh.read()

    html_text = None
    if args.html:
        with open(args.html, "r", encoding="utf-8") as fh:
            html_text = fh.read()

    recipe = build_recipe(args.url, text, html_text=html_text, fetch_image=not args.no_image)

    out = args.out or f"{recipe.name.replace('/', '-')}.paprikarecipes"
    recipe.save(out)
    if not out.endswith(".paprikarecipes"):
        out += ".paprikarecipes"
    print(f"Wrote {out}")
    print(f"  name:       {recipe.name}")
    print(f"  servings:   {recipe.servings}")
    print(f"  times:      prep={recipe.prep_time!r} total={recipe.total_time!r}")
    print(f"  difficulty: {recipe.difficulty}")
    print(f"  rating:     {recipe.rating}")
    print(f"  categories: {recipe.categories}")
    print(f"  ingredients: {len(recipe.ingredients.splitlines())} lines")
    print(f"  directions:  {len(recipe.directions.split(chr(10)+chr(10)))} steps")
    print(f"  pictures:   {1 + len(recipe.photos) if recipe.photo_bytes else 0}")
    print(f"  description: {recipe.description or '(none)'}")
    print(f"  nutrition:  {'(from Meine Notizen)' if recipe.nutritional_info else '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
