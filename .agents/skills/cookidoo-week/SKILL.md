---
name: cookidoo-week
description: Plan and execute the user's recurring Cookidoo meal-prep week. Use when the user invokes $cookidoo-week, asks for the next Cookidoo weekly plan, or wants three new Cookidoo recipes with notes, portion targets, nutrition estimates, shopping-list cleanup, pantry handling, and week-plan/list setup.
---

# Cookidoo Week

## Token Efficiency

Respond like smart caveman. Cut all filler, keep technical substance.
- Drop articles (a, an, the), filler (just, really, basically, actually).
- Drop pleasantries (sure, certainly, happy to).
- No hedging. Fragments fine. Short synonyms.
- Technical terms stay exact. Code blocks unchanged.
- Pattern: [thing] [action] [reason]. [next step].

## Scope

Run recurring Cookidoo workflow end to end: pick three new recipes, calculate realistic portions and nutrition labels, write Cookidoo notes, create custom list, clear/rebuild shopping list, apply pantry cleanup, add meals to week plan.

Project root: three dirs up from this `SKILL.md`. Use that root for `docs/`, `data/`, `bin/`, `recipes/`, `reports/`.

## Browser

- Use in-app browser for Cookidoo.
- If browser automation needed, use Browser Use plugin/tooling; read its skill before first browser API action.
- Treat user logged in only after current browser session proves it. Otherwise ask user to log in; continue after confirmation.
- Do not use generic internet search instead of logged-in Cookidoo for recipe details, ratings, shopping-list actions, notes, or week-plan changes.
- For repeated Cookidoo UI actions, load `references/browser-helpers.md`; copy only smallest relevant snippet into browser context.

## Context Discipline

- Do not broad-search `data/products_harmonized.json`; use focused `bin/nutrition.py search "<ingredient>" --source ...`.
- Keep browser observations compact: list count, saved-note substring, recipe/date presence, pantry-staple absence.
- If UI state unclear, inspect smallest relevant DOM/snapshot excerpt.
- Read large local references, including Browser instructions, once per turn unless changed.
- After `bin/nutrition.py week-brief`, keep later checks targeted to relevant section/substrings. Do not repeat full brief unless final answer or audit needs it.
- For repetitive Cookidoo actions, prefer small reusable page helpers and targeted JavaScript checks over repeated full snapshots.

## Week Rule

Meal-prep week: Saturday through Friday. Cook Saturday, Sunday, Monday. Three recipes should yield three real meal-prep portions each, nine meals total:

- user gets seven meals
- user's father eats one and takes one
- recipes planned as Saturday, Sunday, Monday entries
- Monday usually gets lowest-effort recipe: short active time, little chopping, little cleanup, few nested side steps
- Monday category not fixed; select one fish, one meat, one vegetarian, then place easiest recipe on Monday when possible

No target week: choose next Saturday after current date. State exact Saturday-Friday date range.

## Recipe Selection

Pick exactly three Cookidoo recipes:

1. one fish dish
2. one meat dish
3. one vegetarian dish

Criteria:

- Difficulty should be `einfach`.
- Prep low; prefer `Arbeitszeit` around 30 minutes or less unless clearly easy.
- Monday: prefer `Arbeitszeit` around 20-25 minutes or less, few ingredients, little chopping, low cleanup.
- Target normal satisfying meals around 600-800 kcal per real meal-prep portion; slightly above acceptable if dish fits.
- Protein: prefer at least 40 g per real portion.
- 30-39 g protein acceptable when recipe otherwise fits.
- Below 25 g protein only deliberate exception, e.g. seasonal dish; mark in Cookidoo note and final response.
- Protein-forward, not fitness/protein-bomb optimized.
- Avoid poor ratings. Prefer about 4.3+ stars with plausible rating count; reject low-rated recipes unless strong reason and tell user.
- Avoid any recipe already used this year. Check `docs/meal-plan-history-2026.md`, artifacts in `recipes/` and `reports/`, and relevant Cookidoo lists/history visible in browser. Compare title and recipe ID.
- Use light seasonality when natural; do not force.
- Use one listed/clickable Cookidoo portion count that fits target real portions and calorie range.
- Do not use custom unlisted portion count via `Portionsgröße anpassen`/`Meine Kreationen`.
- If three real portions map to four listed Cookidoo portions, use four Cookidoo portions and note four Cookidoo portions become three real meal-prep portions.

## Nutrition

Read `docs/nutrition-workflow.md`. Use `bin/nutrition.py`.

Cookidoo nutrition values: comparison only when visible ingredients can be calculated locally. Primary note uses local ingredient calculation.

Matching:

- BLS for generic raw/common ingredients: vegetables, raw meat/fish, rice, potatoes, butter, cream, cheese.
- REWE/Edeka/dm/product entries for product-like ingredients: wraps, canned goods, passata, branded sauces, Cookidoo-specific wording.
- Keep every matched `source` and `id` in recipe JSON.
- Use `data/ingredient-defaults.json` for known ambiguous ingredients.
- Cookidoo vegetable broth paste/cubes without specific product: use `rewe:2082415` (`Podravka Vegeta Oryginalna 500g`); assume `1 geh. TL` about `10 g` unless weight given.
- Model explicit salt separately. Salt, broth paste, stock cubes, canned products, "to taste" additions are weakest estimate.
- Pick realistic products user would likely buy. Do not force matches to reproduce Cookidoo totals.

For each recipe:

1. create/update recipe artifact under `recipes/`
2. calculate nutrition with `bin/nutrition.py calc`
3. write/update report under `reports/`
4. decide Cookidoo portion count and real meal-prep portion count
5. note important assumptions and large Cookidoo-vs-local discrepancy

After recipe JSON ready, run `bin/nutrition.py week-brief recipes/<file>.json --date YYYY-MM-DD` for compact summary, Cookidoo note text, pantry precheck, final checklist.

For pantry-only zero-gram ingredients, use `pantry_names` in recipe JSON when automatic split would be ambiguous. Helper already avoids splitting descriptive suffixes such as `Lorbeerblatt, getrocknet`.

## Note Format

Use German note text with blank lines and German nutrition-label wording. Put full match tables in report, not Cookidoo notes.

Template:

```text
KW XX (DD.-DD.MM.): Samstag Fisch. 4 Cookidoo-Portionen kochen -> 3 Wochenportionen.

Nährwerte geschätzt (BLS/REWE, Salz grob), je Wochenportion:
Energie 3134 kJ / 749 kcal
Fett 34,3 g
  davon gesättigte Fettsäuren 10,8 g
Kohlenhydrate 53,2 g
  davon Zucker 6,3 g
Ballaststoffe 9,0 g
Eiweiß 51,9 g
Salz 2,8 g

Einfrieren: eher nicht ideal; zuerst/zeitnah essen.
```

Adjust first line for Saturday/Sunday/Monday, fish/meat/vegetarian, exact dates, Cookidoo portion count, real meal-prep portion count. Always include short freezing/storage judgment.

## Pantry And Shopping List

Read `data/pantry.json` and `docs/nutrition-workflow.md` before shopping-list cleanup.

Always available unless pantry says otherwise:

- Wasser
- Olivenöl
- Öl when Cookidoo wording can be satisfied with pantry Rapsöl
- Butter when Cookidoo wording can be satisfied with ungesalzene Butter
- Essig when Cookidoo wording can be satisfied with weißer Essig
- Pfeffer when Cookidoo wording can be satisfied with schwarzer Pfeffer
- Salz
- dated spices/sauces present and not expired by first cooking date

Do not remove Sonnenblumenöl or other non-standard oils unless `pantry.json` explicitly covers them. Do not remove specialty vinegar such as Reisessig unless pantry says available and suitable. Unknown expiry: keep on list or flag manual review.

Use `bin/nutrition.py pantry-check "<Cookidoo ingredient>" --date YYYY-MM-DD` for individual shopping-list decisions.

## Paprika Export

When adding each recipe to `Meine Woche`, also run:

`python3 cookidoo_text_to_paprika.py --url "$current_url" --text page.txt --html page.html --out "$recipe_title.paprikarecipes"`

`page.txt` = rendered select-all copy; `page.html` = current `document.documentElement.outerHTML`; `--url` = final variant URL.

## Cookidoo UI Workflow

Read `docs/cookidoo-ui-reference.md` before manipulating Cookidoo.

Steps:

1. Clear current Cookidoo shopping list before adding recipes, so stale checked items cannot remain.
2. Create Cookidoo custom list for target week, e.g. `KW 20 (09.-15.05.)`.
3. Add exactly three selected recipes to list.
4. For each recipe, use only listed/clickable Cookidoo portion count. Do not create custom unlisted portion adaptations.
5. Add note text to each recipe.
6. Add three recipes to shopping list.
7. Remove/check off pantry-covered ingredients using pantry rules.
8. Add recipes to Cookidoo week plan on Saturday, Sunday, Monday; for each item added, run Paprika export from current finalized recipe page.
9. Verify custom list has exactly three recipes, week plan has three correct dates, notes are saved, Paprika files exist, shopping list lacks pantry staples.

If Cookidoo UI behavior differs from docs, adapt to current UI and update `docs/cookidoo-ui-reference.md`.

## Final Response

Report:

- date/day/category
- Cookidoo portion count and real meal-prep portion count
- estimated kcal and protein per real portion
- freezing/storage note
- rejected or caveat-worthy items, especially rating/nutrition discrepancies
- confirmation: list, notes, Paprika exports, week plan, shopping list, pantry cleanup completed

If live Cookidoo step failed, state exact pending step and reason.
