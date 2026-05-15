#!/usr/bin/env python3
"""Small local nutrition helper for Cookidoo meal planning.

It reads the harmonized nutrition data generated from the sibling rewe project and
supports two LLM-friendly workflows:

  nutrition.py search "broccoli roh" --source bls
  nutrition.py calc recipes/kw19-20-2026.json --markdown
  nutrition.py week-brief recipes/kw19-20-2026.json --date 2026-05-09
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "products_harmonized.json"
DEFAULT_PANTRY = Path(__file__).resolve().parents[1] / "data" / "pantry.json"
NUTRIENTS = [
    "kcal",
    "carbs",
    "sugar",
    "protein",
    "fat",
    "saturated_fat",
    "fiber",
    "salt",
]
LABELS = {
    "kcal": "kcal",
    "carbs": "KH",
    "sugar": "Zucker",
    "protein": "Eiweiß",
    "fat": "Fett",
    "saturated_fat": "ges. FS",
    "fiber": "Ballastst.",
    "salt": "Salz",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


PANTRY_DESCRIPTOR_PARTS = {
    normalize(value)
    for value in (
        "abgezupft",
        "frisch",
        "gehackt",
        "gemahlen",
        "gerebelt",
        "getrocknet",
        "grob zerkleinert",
        "in Stuecken",
        "in Stücken",
        "kuehlschrankkalt",
        "kühlschrankkalt",
        "ohne Stiele",
        "optional",
        "selbst gemacht",
    )
}


def is_pantry_descriptor_part(value: str) -> bool:
    return normalize(value) in PANTRY_DESCRIPTOR_PARTS


def load_products(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def product_key(product: dict[str, Any]) -> tuple[str, str]:
    return (product["source"], product["id"])


def nutrient(product: dict[str, Any], key: str) -> float:
    value = product.get("nutrients", {}).get(key)
    if value is None:
        return 0.0
    return float(value)


def fmt(value: float, digits: int = 1) -> str:
    if abs(value) < 0.005:
        value = 0.0
    if digits == 0:
        return str(int(round(value)))
    return f"{value:.{digits}f}".replace(".", ",")


def search(args: argparse.Namespace) -> int:
    products = load_products(args.db)
    terms = normalize(args.query).split()
    rows = []
    for product in products:
        if args.source and product["source"] != args.source:
            continue
        haystack = normalize(" ".join([
            product.get("title", ""),
            product.get("brand", ""),
            " ".join(product.get("categories", [])),
        ]))
        if all(term in haystack for term in terms):
            rows.append(product)

    source_priority = {"bls": 0, "rewe": 1, "edeka": 2, "dm": 3}
    rows.sort(key=lambda p: (source_priority.get(p["source"], 9), len(p.get("title", ""))))

    print("source\tid\ttitle\tkcal\tprotein\tcarbs\tsugar\tfat\tsat_fat\tfiber\tsalt")
    for product in rows[: args.limit]:
        ns = product.get("nutrients", {})
        print("\t".join([
            product["source"],
            product["id"],
            product["title"],
            str(ns.get("kcal", "")),
            str(ns.get("protein", "")),
            str(ns.get("carbs", "")),
            str(ns.get("sugar", "")),
            str(ns.get("fat", "")),
            str(ns.get("saturated_fat", "")),
            str(ns.get("fiber", "")),
            str(ns.get("salt", "")),
        ]))
    return 0


def load_pantry(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"Invalid date {value!r}; expected YYYY-MM-DD") from exc


def pantry_entries(pantry: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for section in ("always_have", "not_always_have", "dated_items"):
        for entry in pantry.get(section, []):
            rows.append((section, entry))
    return rows


def match_pantry_item(ingredient: str, pantry: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    query = normalize(ingredient)
    query_words = set(query.split())
    best: tuple[int, str, dict[str, Any]] | None = None
    for section, entry in pantry_entries(pantry):
        aliases = [entry.get("name", ""), *entry.get("aliases", [])]
        for alias in aliases:
            candidate = normalize(alias)
            candidate_words = set(candidate.split())
            if not candidate:
                continue
            if query == candidate:
                score = 0
            elif candidate_words and candidate_words.issubset(query_words):
                score = 1
            elif len(query_words) > 1 and query_words.issubset(candidate_words):
                score = 2
            else:
                continue
            if best is None or score < best[0]:
                best = (score, section, entry)
    if best is None:
        return None
    return best[1], best[2]


def pantry_decision(ingredient: str, pantry: dict[str, Any], cook_date: dt.date) -> dict[str, Any]:
    matched = match_pantry_item(ingredient, pantry)
    if not matched:
        return {
            "ingredient": ingredient,
            "action": "buy_or_match_manually",
            "reason": "not found in pantry",
        }

    section, entry = matched
    result = {
        "ingredient": ingredient,
        "matched": entry["name"],
        "cookidoo_name": entry.get("cookidoo_name", entry["name"]),
        "section": section,
    }

    if section == "always_have":
        result.update({
            "action": "remove_from_shopping_list",
            "reason": entry.get("shopping_policy", "usually_have"),
        })
    elif section == "not_always_have":
        result.update({
            "action": "keep_on_shopping_list",
            "reason": entry.get("notes", "not a pantry default"),
        })
    else:
        expires = entry.get("expires")
        if not expires:
            result.update({
                "action": "review_manually",
                "expires": None,
                "reason": "expiry unknown",
            })
        else:
            expiry_date = parse_date(expires)
            result["expires"] = expires
            if expiry_date >= cook_date:
                result.update({
                    "action": "remove_from_shopping_list",
                    "reason": f"in pantry and valid on {cook_date.isoformat()}",
                })
            else:
                result.update({
                    "action": "keep_on_shopping_list",
                    "reason": f"expired before {cook_date.isoformat()}",
                })
    return result


def pantry_check(args: argparse.Namespace) -> int:
    pantry = load_pantry(args.pantry)
    cook_date = parse_date(args.date)
    for ingredient in args.ingredients:
        decision = pantry_decision(ingredient, pantry, cook_date)
        if args.json:
            print(json.dumps(decision, ensure_ascii=False))
        else:
            matched = ""
            if "matched" in decision:
                label = decision.get("cookidoo_name") or decision["matched"]
                if normalize(label) != normalize(decision["matched"]):
                    label = f"{label} / Vorrat: {decision['matched']}"
                matched = f" -> {label}"
            print(f"{ingredient}{matched}: {decision['action']} ({decision['reason']})")
    return 0


@dataclass
class LineResult:
    name: str
    grams: float
    product: dict[str, Any] | None
    nutrients: dict[str, float]
    note: str


def calc_line(item: dict[str, Any], index: dict[tuple[str, str], dict[str, Any]]) -> LineResult:
    grams = float(item.get("grams") or 0)
    note = item.get("note", "")
    product = None
    nutrients = {key: 0.0 for key in NUTRIENTS}

    if "manual_nutrients_per_100g" in item:
        source = item["manual_nutrients_per_100g"]
        for key in NUTRIENTS:
            nutrients[key] = float(source.get(key, 0.0)) * grams / 100.0
    elif item.get("source") and item.get("id"):
        key = (item["source"], item["id"])
        product = index.get(key)
        if not product:
            raise SystemExit(f"Product not found: {key} for {item.get('name')}")
        for key_name in NUTRIENTS:
            nutrients[key_name] = nutrient(product, key_name) * grams / 100.0

    return LineResult(
        name=item.get("name", ""),
        grams=grams,
        product=product,
        nutrients=nutrients,
        note=note,
    )


def sum_nutrients(lines: list[LineResult]) -> dict[str, float]:
    total = {key: 0.0 for key in NUTRIENTS}
    for line in lines:
        for key in NUTRIENTS:
            total[key] += line.nutrients[key]
    return total


def label_text(values: dict[str, float]) -> str:
    parts = [
        f"{fmt(values['kcal'], 0)} kcal",
        f"KH {fmt(values['carbs'])} g",
        f"Zucker {fmt(values['sugar'])} g",
        f"Eiweiß {fmt(values['protein'])} g",
        f"Fett {fmt(values['fat'])} g",
        f"ges. FS {fmt(values['saturated_fat'])} g",
        f"Ballastst. {fmt(values['fiber'])} g",
        f"Salz {fmt(values['salt'])} g",
    ]
    return " | ".join(parts)


def nutrition_label_text(values: dict[str, float]) -> str:
    kj = values["kcal"] * 4.184
    lines = [
        f"Energie {fmt(kj, 0)} kJ / {fmt(values['kcal'], 0)} kcal",
        f"Fett {fmt(values['fat'])} g",
        f"  davon gesättigte Fettsäuren {fmt(values['saturated_fat'])} g",
        f"Kohlenhydrate {fmt(values['carbs'])} g",
        f"  davon Zucker {fmt(values['sugar'])} g",
        f"Ballaststoffe {fmt(values['fiber'])} g",
        f"Eiweiß {fmt(values['protein'])} g",
        f"Salz {fmt(values['salt'])} g",
    ]
    return "\n".join(lines)


def calc_recipe(recipe: dict[str, Any], index: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    lines = [calc_line(item, index) for item in recipe["ingredients"]]
    total = sum_nutrients(lines)
    cookidoo_portions = float(recipe["cookidoo_portions"])
    real_portions = float(recipe.get("real_portions") or cookidoo_portions)
    per_cookidoo = {key: value / cookidoo_portions for key, value in total.items()}
    per_real = {key: value / real_portions for key, value in total.items()}
    return {
        "recipe": recipe,
        "lines": lines,
        "total": total,
        "per_cookidoo": per_cookidoo,
        "per_real": per_real,
    }


def markdown_report(results: list[dict[str, Any]]) -> str:
    out = ["# Cookidoo nutrition estimate", ""]
    for result in results:
        recipe = result["recipe"]
        out.append(f"## {recipe['title']}")
        out.append("")
        out.append(f"- URL: {recipe['url']}")
        out.append(f"- Cookidoo-Portionen: {recipe['cookidoo_portions']}")
        out.append(f"- Echte Mealprep-Portionen: {recipe.get('real_portions', recipe['cookidoo_portions'])}")
        if recipe.get("cookidoo_nutrition_per_portion"):
            cd = recipe["cookidoo_nutrition_per_portion"]
            out.append(
                "- Cookidoo pro Portion: "
                f"{fmt(cd.get('kcal', 0), 0)} kcal | "
                f"KH {fmt(cd.get('carbs', 0))} g | "
                f"Eiweiß {fmt(cd.get('protein', 0))} g | "
                f"Fett {fmt(cd.get('fat', 0))} g | "
                f"Ballastst. {fmt(cd.get('fiber', 0))} g"
            )
        out.append(f"- Geschätzt pro Cookidoo-Portion: {label_text(result['per_cookidoo'])}")
        out.append(f"- Geschätzt pro echter Portion: {label_text(result['per_real'])}")
        if recipe.get("freezer_note"):
            out.append(f"- Einfrieren: {recipe['freezer_note']}")
        if recipe.get("note"):
            out.append(f"- Hinweis: {recipe['note']}")
        out.append("")
        out.append("| Zutat | Menge | Match | kcal | Eiweiß | KH | Zucker | Fett | Salz |")
        out.append("|---|---:|---|---:|---:|---:|---:|---:|---:|")
        for line in result["lines"]:
            match = "ignoriert"
            if line.product:
                match = f"{line.product['source']}:{line.product['id']} {line.product['title']}"
            elif line.note:
                match = line.note
            out.append(
                f"| {line.name} | {fmt(line.grams)} g | {match} | "
                f"{fmt(line.nutrients['kcal'], 0)} | "
                f"{fmt(line.nutrients['protein'])} | "
                f"{fmt(line.nutrients['carbs'])} | "
                f"{fmt(line.nutrients['sugar'])} | "
                f"{fmt(line.nutrients['fat'])} | "
                f"{fmt(line.nutrients['salt'])} |"
            )
        out.append("")
        out.append("Notizvorschlag:")
        out.append("")
        out.append("```text")
        out.append(recipe_note(result))
        out.append("```")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def recipe_note(result: dict[str, Any]) -> str:
    recipe = result["recipe"]
    if recipe.get("cookidoo_note"):
        return recipe["cookidoo_note"]
    week = recipe.get("week_label", "Mealprep")
    category = recipe.get("category", "")
    cookidoo_portions = int(recipe["cookidoo_portions"])
    real_portions = int(recipe.get("real_portions") or recipe["cookidoo_portions"])
    real = nutrition_label_text(result["per_real"])
    freezer = recipe.get("freezer_note", "")
    extra = recipe.get("note", "")
    estimate_context = recipe.get("estimate_context", "BLS/REWE, Salz grob")
    parts = [
        f"{week}: {category}. {cookidoo_portions} Cookidoo-Portionen kochen -> {real_portions} Wochenportionen.",
        f"Nährwerte geschätzt ({estimate_context}), je Wochenportion:\n{real}",
    ]
    if freezer:
        parts.append(f"Einfrieren: {freezer}.")
    if extra:
        parts.append(extra)
    return "\n\n".join(part for part in parts if part).strip()


def pantry_ingredient_names(item: dict[str, Any]) -> list[str]:
    pantry_names = item.get("pantry_names")
    if isinstance(pantry_names, list):
        return [str(part).strip() for part in pantry_names if str(part).strip()]

    name = item.get("name", "").strip()
    if not name:
        return []
    if normalize(name) == "garflussigkeit":
        return []
    if float(item.get("grams") or 0) == 0 and ("," in name or " und " in name):
        parts = [part.strip() for part in re.split(r",|\bund\b", name) if part.strip()]
        if len(parts) > 1 and all(is_pantry_descriptor_part(part) for part in parts[1:]):
            return [name]
        return parts
    return [name]


def calc(args: argparse.Namespace) -> int:
    products = load_products(args.db)
    index = {product_key(product): product for product in products}
    with Path(args.recipe_file).open(encoding="utf-8") as handle:
        data = json.load(handle)
    recipes = data["recipes"] if isinstance(data, dict) and "recipes" in data else data
    results = [calc_recipe(recipe, index) for recipe in recipes]

    if args.markdown:
        sys.stdout.write(markdown_report(results))
    else:
        for result in results:
            print(result["recipe"]["title"])
            print("  pro Cookidoo-Portion:", label_text(result["per_cookidoo"]))
            print("  pro Wochenportion:   ", label_text(result["per_real"]))
            print("  note:", recipe_note(result))
    return 0


def week_brief(args: argparse.Namespace) -> int:
    products = load_products(args.db)
    index = {product_key(product): product for product in products}
    pantry = load_pantry(args.pantry)
    cook_date = parse_date(args.date)

    with Path(args.recipe_file).open(encoding="utf-8") as handle:
        data = json.load(handle)
    recipes = data["recipes"] if isinstance(data, dict) and "recipes" in data else data
    results = [calc_recipe(recipe, index) for recipe in recipes]

    out = ["# Cookidoo week brief", ""]
    if isinstance(data, dict) and data.get("week"):
        out.extend([f"- Woche: {data['week']}", ""])

    out.extend([
        "## Summary",
        "",
        "| Tag/Kategorie | Rezept | Portionen | kcal | Eiweiß | Einfrieren |",
        "|---|---|---:|---:|---:|---|",
    ])
    for result in results:
        recipe = result["recipe"]
        out.append(
            "| "
            f"{recipe.get('category', '')} | "
            f"{recipe['title']} | "
            f"{recipe['cookidoo_portions']} -> {recipe.get('real_portions', recipe['cookidoo_portions'])} | "
            f"{fmt(result['per_real']['kcal'], 0)} | "
            f"{fmt(result['per_real']['protein'])} g | "
            f"{recipe.get('freezer_note', '')} |"
        )

    out.extend(["", "## Cookidoo Notes", ""])
    for result in results:
        out.extend([
            f"### {result['recipe']['title']}",
            "",
            "```text",
            recipe_note(result),
            "```",
            "",
        ])

    decisions: dict[str, dict[str, Any]] = {}
    for recipe in recipes:
        for ingredient in recipe.get("ingredients", []):
            for name in pantry_ingredient_names(ingredient):
                decision = pantry_decision(name, pantry, cook_date)
                key = normalize(decision["ingredient"])
                decisions.setdefault(key, decision)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for decision in decisions.values():
        grouped.setdefault(decision["action"], []).append(decision)

    out.extend([
        "## Pantry Precheck",
        "",
        "Use Cookidoo's visible shopping-list wording as the final source of truth.",
        "",
    ])
    for action, heading in [
        ("remove_from_shopping_list", "Check off/remove"),
        ("keep_on_shopping_list", "Keep"),
        ("review_manually", "Review manually"),
        ("buy_or_match_manually", "Buy or match manually"),
    ]:
        rows = sorted(grouped.get(action, []), key=lambda row: normalize(row["ingredient"]))
        if not rows:
            continue
        out.extend([f"### {heading}", ""])
        for row in rows:
            matched = row.get("cookidoo_name") or row.get("matched")
            suffix = f" -> {matched}" if matched else ""
            out.append(f"- {row['ingredient']}{suffix}: {row['reason']}")
        out.append("")

    titles = ", ".join(recipe["title"] for recipe in recipes)
    recipe_count = len(recipes)
    out.extend([
        "## Verification Checklist",
        "",
        "- [ ] Shopping list cleared before adding recipes",
        f"- [ ] Custom list contains exactly: {titles}",
        "- [ ] Notes contain the kcal/protein values from this brief",
        "- [ ] Week plan has Saturday/Sunday/Monday entries",
        f"- [ ] Shopping list shows `Nach Rezepten {recipe_count}`",
        "- [ ] Pantry-covered staples are no longer in the active shopping section",
    ])

    sys.stdout.write("\n".join(out).rstrip() + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--pantry", type=Path, default=DEFAULT_PANTRY)
    sub = parser.add_subparsers(dest="command", required=True)

    search_parser = sub.add_parser("search", help="Search the local nutrition database")
    search_parser.add_argument("query")
    search_parser.add_argument("--source", choices=["bls", "rewe", "edeka", "dm", "bbdepot", "ruehl24", "mcdonalds", "burgerking", "nordsee"])
    search_parser.add_argument("--limit", type=int, default=25)
    search_parser.set_defaults(func=search)

    calc_parser = sub.add_parser("calc", help="Calculate nutrition for a recipe JSON")
    calc_parser.add_argument("recipe_file")
    calc_parser.add_argument("--markdown", action="store_true")
    calc_parser.set_defaults(func=calc)

    brief_parser = sub.add_parser("week-brief", help="Create a compact week summary, notes, pantry precheck, and verification checklist")
    brief_parser.add_argument("recipe_file")
    brief_parser.add_argument("--date", required=True, help="First cooking date, YYYY-MM-DD")
    brief_parser.set_defaults(func=week_brief)

    pantry_parser = sub.add_parser("pantry-check", help="Check whether pantry items should be bought")
    pantry_parser.add_argument("ingredients", nargs="+")
    pantry_parser.add_argument("--date", required=True, help="First cooking date, YYYY-MM-DD")
    pantry_parser.add_argument("--json", action="store_true")
    pantry_parser.set_defaults(func=pantry_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
