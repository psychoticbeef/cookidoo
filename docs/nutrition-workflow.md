# Nutrition Workflow

Goal: estimate German-style nutrition label for Cookidoo mealprep portions; write compact auditable summary into recipe notes.

## Data Sources

- Primary database: `data/products_harmonized.json`
- SQLite/SwiftData copy: `data/products.store`
- Default ingredient matches: `data/ingredient-defaults.json`
- Pantry/shopping defaults: `data/pantry.json`
- Sources: REWE, Edeka, dm, BLS 2025, few restaurant/product sources
- CLI helper: `bin/nutrition.py`

## Portion Rule

Current mealprep setup: most recipes cooked as 4 Cookidoo portions, divided into 3 real weekly meals.

Formula:

```text
per real meal = total recipe nutrition / real meal count
per Cookidoo portion = total recipe nutrition / Cookidoo portion count
```

## Protein Target

Weekly mealprep: prefer at least 40 g protein per real meal. Accept 30-39 g when recipe otherwise fits. Below 25 g only deliberate exception, e.g. seasonal dish; mark exception in Cookidoo note.

Do not turn workflow into fitness-recipe optimization. Target: normal satisfying food with meaningfully higher protein than typical easy dinner.

## Cookidoo Values

Cookidoo nutrition values are comparison data, not primary estimate, when ingredient amounts exist. Primary note uses local calculation from `bin/nutrition.py`. Use Cookidoo values for sanity checks; mention comparison when divergence matters.

Reason: Cookidoo values can be hard to reconcile with visible ingredients. Example: `r251327` (Corn Chowder) showed 685 kcal per Cookidoo portion, while local calculation with regular `Bacon in Streifen` matched to REWE Tulip Baconstreifen gave about 497 kcal per Cookidoo portion. Very fatty Pancetta/Bauchspeck still stayed below Cookidoo. In such cases:

1. Pick ingredient match reflecting likely real purchase, not match that forces Cookidoo total.
2. State key assumption in note, e.g. "Bacon als regulaere Baconstreifen, ausgelassenes Fett bleibt im Gericht".
3. Adjust `real_portions` so actual meal lands in 600-800 kcal target.
4. Keep Cookidoo values only as comparison text when helpful.

## Matching Rules

1. Use BLS for generic raw/common ingredients.
2. Use supermarket products when ingredient is product-like or branded.
3. Ignore water and tiny herb/spice garnish unless material.
4. Model explicit salt separately with BLS table salt.
5. Treat broth paste/cubes as rough salt estimates; brands and homemade paste vary heavily.
6. Check `data/ingredient-defaults.json` for known ambiguous ingredients.
7. When Cookidoo says vegetable broth paste/cube and no exact product is given, use `rewe:2082415` (`Podravka Vegeta Oryginalna 500g`) as default model. Assume `1 geh. TL` roughly `10 g` unless recipe gives weight.
8. Record every match by `source` and `id` in recipe JSON.

## Pantry And Shopping List

Before final Cookidoo shopping list, compare ingredient list against `data/pantry.json`.

Always available unless explicitly overridden:

- Wasser
- Olivenöl
- Öl (pantry: Rapsöl)
- Butter (pantry: ungesalzene Butter)
- Essig (pantry: weißer Essig)
- Pfeffer (pantry: schwarzer Pfeffer)
- Salz

Do not treat Sonnenblumenöl as pantry default. If recipe asks for Sonnenblumenöl or another non-standard oil, leave it on shopping list.

Use Cookidoo shopping-list wording in `cookidoo_name`; actual pantry item in `name`. This keeps UI cleanup simple while preserving substitutions such as `Öl -> Rapsöl` and `Gewürzpaste für Gemüsebrühe, selbst gemacht -> Vegeta`.

Recipe JSON: zero-gram ingredient can mark pantry-only item. `week-brief` splits compact zero-gram pantry lists such as `Paprika edelsüß, Pfeffer, Muskat` into separate checks. It keeps descriptive suffixes such as `Lorbeerblatt, getrocknet` as one ingredient so adjectives do not become bogus shopping-list entries. If automatic split stays ambiguous, add explicit override:

```json
{"name": "Paprika edelsüß, Pfeffer und Muskat", "grams": 0, "pantry_names": ["Paprika edelsüß", "Pfeffer", "Muskat"]}
```

Dated spices/sauces:

1. Ingredient listed and `expires` after first cooking date: remove from shopping list.
2. `expires` before cooking date: keep and mark `nachkaufen`.
3. `expires` is `null`: keep or flag manual review; do not remove blindly.
4. Preserve exact recipe requirements when substitution changes dish materially, e.g. Reisessig is not weißer Essig.

Current expiry parsing:

- `27` means `2027-12-31`.
- `08/28` means `2028-08-31`.
- `ende 26` means `2026-12-31`.
- `?` means unknown/manual review.

CLI checks:

```sh
bin/nutrition.py pantry-check "Paprika edelsüß" --date 2026-05-09
bin/nutrition.py pantry-check "Sonnenblumenöl" --date 2026-05-09
bin/nutrition.py pantry-check "Reisessig" --date 2026-05-09
```

## Note Format

Use short Cookidoo note:

```text
KW 19-20 (09.-15.05.): Samstag Fisch. 4 Cookidoo-Portionen kochen -> 3 Wochenportionen.

Nährwerte geschätzt (BLS/REWE, Salz grob), je Wochenportion:
Energie 3134 kJ / 749 kcal
Fett 34,3 g
  davon gesättigte Fettsäuren 10,8 g
Kohlenhydrate 53,2 g
  davon Zucker 6,3 g
Ballaststoffe 9,0 g
Eiweiß 51,9 g
Salz 2,8 g

Einfrieren: eher nicht ideal; Fisch zuerst/zeitnah essen.
```

Keep full ingredient-match table in `reports/`, not Cookidoo.

## Caveats

- Cookidoo gives only subset of label values. Sugar, saturated fat, salt are local estimates.
- Salt usually weakest estimate because broth paste, stock cubes, canned products, "to taste" additions vary.
- Estimate sanity-checks meal size; not medical-grade nutrition tracking.
