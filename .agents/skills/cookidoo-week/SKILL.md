---
name: cookidoo-week
description: Plan and execute the user's recurring Cookidoo meal-prep week. Use when the user invokes $cookidoo-week, asks for the next Cookidoo weekly plan, or wants three new Cookidoo recipes with notes, portion targets, nutrition estimates, shopping-list cleanup, pantry handling, and week-plan/list setup.
---

# Cookidoo Week

## Overview

Execute the recurring Cookidoo workflow end to end: select three new recipes, calculate realistic meal portions and nutrition labels, write Cookidoo notes, create a custom list, clear/rebuild the shopping list, apply pantry cleanup, and add the meals to the Cookidoo week plan.

Resolve the Cookidoo project root by going three directories up from this `SKILL.md` file. Use that project root for `docs/`, `data/`, `bin/`, `recipes/`, and `reports/`.

## Before Browser Work

Use the in-app browser for Cookidoo. If browser automation is needed, use the Browser Use plugin/tooling and follow its skill instructions before the first browser API action. Assume the user is logged in only when the current browser session confirms it; otherwise ask the user to log in and continue after they say it is done.

Do not use generic internet search as a substitute for the user's logged-in Cookidoo account when recipe details, ratings, shopping-list actions, notes, or week-plan changes are needed.

For repeated Cookidoo UI actions, load `references/browser-helpers.md` and copy
only the smallest relevant snippet into the browser context.

## Context Discipline

- Do not run broad `rg` searches over `data/products_harmonized.json`; use focused `bin/nutrition.py search "<ingredient>" --source ...` queries instead.
- Keep browser observations compact. Prefer targeted checks such as list count, saved-note substring, recipe/date presence, and pantry-staple absence over dumping full page text or large DOM snapshots.
- If a browser UI state is unclear, inspect only the smallest relevant DOM/snapshot excerpt needed for the next action.
- Read large local references, including this skill's Browser instructions, once per turn unless they changed. Reuse the remembered workflow instead of reopening the same long files.
- After running `bin/nutrition.py week-brief`, keep later checks targeted to the relevant section or substring. Do not repeat the full brief output unless it is needed for the final answer or an audit artifact.
- For repetitive Cookidoo browser actions, prefer small reusable page helpers and targeted JavaScript checks over repeated full snapshots.

## Week Rule

The user's meal-prep week runs Saturday through Friday. They cook on Saturday, Sunday, and Monday. Each of the three recipes should yield three real meal-prep portions, for nine total meals:

- the user gets seven meals
- the user's father eats one and takes one
- the recipes should be planned as Saturday, Sunday, and Monday entries
- Monday should usually get the lowest-effort recipe of the three because work/sports make the evening tighter. Prefer short active time, little chopping, little cleanup, and few nested side steps for Monday.
- Do not force a fixed category onto Monday. Select one fish, one meat, and one vegetarian recipe, then assign the easiest/lowest-effort one to Monday when possible.

When invoked without a target week, choose the next Saturday after the current date as the start date and state the exact Saturday-Friday date range. Use absolute dates in user-facing text.

## Recipe Selection

Pick exactly three Cookidoo recipes:

1. one fish dish
2. one meat dish
3. one vegetarian dish

Selection criteria:

- Cookidoo difficulty should be `einfach`.
- Keep prep low; prefer `Arbeitszeit` around 30 minutes or less unless the recipe is otherwise clearly easy.
- For the Monday recipe, prefer even lower effort: ideally `Arbeitszeit` around 20-25 minutes or less, few ingredients, little chopping, and low cleanup.
- Prefer satisfying, normal meals in the rough 600-800 kcal range per real meal-prep portion; slightly above is acceptable when the dish is otherwise a good fit.
- Protein target: prefer at least 40 g protein per real meal-prep portion.
- Accept 30-39 g protein per real portion when the recipe otherwise fits well.
- Treat below 25 g protein as a deliberate exception only, e.g. a seasonal dish, and explicitly mark it in the Cookidoo note and final response.
- Keep the meals protein-forward, but do not optimize for "protein bomb" or fitness recipes.
- Avoid relatively poor ratings. Prefer about 4.3 stars or higher with a plausible number of ratings; reject low-rated recipes unless there is a clear reason and tell the user.
- Avoid repeating any recipe already used this year. Check `docs/meal-plan-history-2026.md`, existing artifacts in `recipes/` and `reports/`, and any relevant Cookidoo lists/history visible in the browser. Compare both title and recipe ID.
- Add light seasonality when it naturally fits. Do not force every recipe to be seasonal, but in season include relevant dishes occasionally, e.g. asparagus in asparagus season.
- Choose recipes where one of Cookidoo's listed/clickable portion counts fits the target real portions and calorie range. Do not use a custom unlisted portion count via `Portionsgröße anpassen`/`Meine Kreationen`; Cookidoo does not provide the same success guarantee for those adaptations and this workflow should avoid them. If the final three real portions correspond to four listed Cookidoo portions, use four Cookidoo portions and note that four Cookidoo portions become three real meal-prep portions.

## Nutrition Calculation

Read `docs/nutrition-workflow.md` and use `bin/nutrition.py` for estimates.

Do not blindly copy Cookidoo nutrition values when the visible ingredients can be calculated locally. Cookidoo values are comparison data only. The primary note should come from the local ingredient calculation.

Matching policy:

- Prefer BLS for generic raw/common ingredients such as vegetables, raw meat/fish, rice, potatoes, butter, cream, and cheese.
- Use REWE/Edeka/dm/product entries for product-like ingredients such as wraps, canned goods, passata, branded sauces, or Cookidoo-specific product wording.
- Keep every matched `source` and `id` in the recipe JSON so the estimate stays auditable.
- Use `data/ingredient-defaults.json` for known ambiguous ingredients.
- For Cookidoo vegetable broth paste/cubes without a specific product, use `rewe:2082415` (`Podravka Vegeta Oryginalna 500g`) and assume `1 geh. TL` is about `10 g` unless the recipe gives a weight.
- Model explicit salt separately. Treat salt, broth paste, stock cubes, canned products, and "to taste" additions as the weakest part of the estimate.
- Pick realistic products the user would likely buy. Do not force ingredient matches to reproduce Cookidoo totals.

For each selected recipe:

1. create or update a recipe artifact under `recipes/`
2. calculate nutrition with `bin/nutrition.py calc`
3. write/update a report under `reports/`
4. decide the Cookidoo portion count and real meal-prep portion count
5. note important assumptions and any large Cookidoo-vs-local discrepancy

After the recipe JSON is ready, run `bin/nutrition.py week-brief recipes/<file>.json --date YYYY-MM-DD` for a compact summary, Cookidoo note text, pantry precheck, and final verification checklist.

For pantry-only zero-gram ingredients, use `pantry_names` in the recipe JSON when
the automatic split would be ambiguous. The helper already avoids splitting
descriptive suffixes such as `Lorbeerblatt, getrocknet`.

## Note Format

Use German note text with blank lines and German nutrition-label wording. Put full match tables in the report, not in Cookidoo notes.

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

Adjust the first line for Saturday/Sunday/Monday, fish/meat/vegetarian, exact dates, Cookidoo portion count, and the real meal-prep portion count. Always include a short freezing/storage judgment.

## Pantry And Shopping List

Read `data/pantry.json` and `docs/nutrition-workflow.md` before cleaning the shopping list.

Always available unless the current pantry file says otherwise:

- Wasser
- Olivenöl
- Öl when Cookidoo's wording can reasonably be satisfied with pantry Rapsöl
- Butter when Cookidoo's wording can reasonably be satisfied with ungesalzene Butter
- Essig when Cookidoo's wording can reasonably be satisfied with weißer Essig
- Pfeffer when Cookidoo's wording can reasonably be satisfied with schwarzer Pfeffer
- Salz
- dated spices/sauces that are present and not expired by the first cooking date

Do not remove Sonnenblumenöl or other non-standard oils unless `pantry.json` explicitly covers them. Do not remove specialty vinegar such as Reisessig unless pantry handling says it is available and suitable. If a pantry item's expiry is unknown, keep it on the list or flag it for manual review instead of removing it silently.

Use `bin/nutrition.py pantry-check "<Cookidoo ingredient>" --date YYYY-MM-DD` for individual shopping-list decisions.

## Cookidoo UI Workflow

Read `docs/cookidoo-ui-reference.md` before manipulating Cookidoo.

Then execute:

1. Clear the current Cookidoo shopping list before adding any new recipes, so stale checked items from a previous week cannot remain.
2. Create a Cookidoo custom list for the target week, e.g. `KW 20 (09.-15.05.)`.
3. Add exactly the three selected recipes to that list.
4. For each recipe, use only a listed/clickable Cookidoo portion count. Do not create custom unlisted portion adaptations.
5. Add the note text to each recipe.
6. Add the three recipes to the shopping list.
7. Remove/check off pantry-covered ingredients using the pantry rules.
8. Add the recipes to the Cookidoo week plan on Saturday, Sunday, and Monday.
9. Verify the custom list has exactly three recipes, the week plan has the three correct dates, notes are saved, and the shopping list no longer contains pantry staples.

If Cookidoo UI behavior differs from the docs, work with the current UI and update `docs/cookidoo-ui-reference.md` with the new learning.

## Final Response

Report the final three recipes with:

- date/day/category
- Cookidoo portion count and real meal-prep portion count
- estimated kcal and protein per real portion
- freezing/storage note
- any rejected or caveat-worthy item, especially rating or nutrition discrepancies
- confirmation that list, notes, week plan, shopping list, and pantry cleanup were completed

If any live Cookidoo step could not be completed, state exactly which step is still pending and why.
